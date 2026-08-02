# db/affiliate_db.py

from __future__ import annotations

import os
import secrets
import string

from datetime import datetime, timedelta
from typing import Optional, Tuple

from configs.logging_setup import log
from database.connection import get_db_cursor


def detect_affiliate_abuse(cursor, user_id, referrer_id, price, now, source_bot):
    """
    Return:
        is_suspicious: bool
        score: int
        reasons: list[str]
    """

    score = 0
    reasons = []

    # =========================================================
    # 1. Referral speed abuse (new user spam)
    # =========================================================
    cursor.execute("""
        SELECT created_at
        FROM users WHERE user_id=%s
    """, (user_id,))
    row = cursor.fetchone()
    if row and row[0]:
        age_minutes = (now - row[0]).total_seconds() / 60
        if age_minutes < 5:
            score += 40
            reasons.append("new_user_too_fast")

    # =========================================================
    # 2. Too many referrals in 1 hour (farming)
    # =========================================================
    cursor.execute("""
        SELECT COUNT(*)
        FROM affiliate_commission_logs
        WHERE referrer_user_id=%s
        AND tx_time > now() - interval '1 hour'
        AND status='paid'
    """, (referrer_id,))
    cnt_hour = cursor.fetchone()[0]
    if cnt_hour >= 3:
        score += 50
        reasons.append("high_hourly_commission_rate")

    # =========================================================
    # 3. Multiple referred users join within short time
    # =========================================================
    cursor.execute("""
        SELECT COUNT(*)
        FROM users
        WHERE referrer_user_id=%s
        AND created_at > now() - interval '10 minutes'
    """, (referrer_id,))
    fast_join = cursor.fetchone()[0]
    if fast_join >= 4:
        score += 40
        reasons.append("multi_fast_signup")

    # =========================================================
    # 4. Commission percentage anomaly
    # =========================================================
    commission = int(price * 0.2)
    if commission > 250_000:  # silakan ubah sesuai bisnis
        score += 30
        reasons.append("abnormal_commission_amount")

    # =========================================================
    # 5. Self-referral (hard block)
    # =========================================================
    if user_id == referrer_id:
        return True, 100, ["self_referral"]

    # =========================================================
    # 6. Known flagged referrer
    # =========================================================
    cursor.execute("""
        SELECT abuse_flag
        FROM users WHERE user_id=%s
    """, (referrer_id,))
    row = cursor.fetchone()
    if row and row[0]:
        return True, 100, ["flagged_referrer"]

    # =========================================================
    # Final Threshold
    # =========================================================
    if score >= 70:
        log.warning(
            f"[AFFILIATE ABUSE] block referrer={referrer_id} user={user_id} score={score} reasons={reasons}"
        )
        return True, score, reasons

    return False, score, reasons


def get_user_by_referral_code(code: str) -> Optional[dict]:
    with get_db_cursor() as (cursor, _):
        cursor.execute(
            "SELECT user_id, affiliate_code, is_active FROM users WHERE affiliate_code=%s",
            (code,)
        )
        row = cursor.fetchone()
        if not row:
            return None
        return {'user_id': row[0], 'affiliate_code': row[1], 'is_active': row[2]}


def get_user_by_referral_code(code: str) -> Optional[dict]:
    with get_db_cursor() as (cursor, _):
        cursor.execute(
            "SELECT user_id, affiliate_code, is_active FROM users WHERE affiliate_code=%s",
            (code,)
        )
        row = cursor.fetchone()
        if not row:
            return None
        return {'user_id': row[0], 'affiliate_code': row[1], 'is_active': row[2]}


# ------------------------------------------------------------------
# DB Fetchers
# ------------------------------------------------------------------

def get_user_by_id(user_id: int) -> Optional[dict]:
    with get_db_cursor() as (cursor, _):
        cursor.execute(
            "SELECT user_id, affiliate_code, referrer_user_id, created_at, is_active FROM users WHERE user_id=%s",
            (user_id,)
        )
        row = cursor.fetchone()
        if not row:
            return None
        return {
            'user_id': row[0],
            'affiliate_code': row[1],
            'referrer_user_id': row[2],
            'created_at': row[3],
            'is_active': row[4],
        }


# ------------------------------------------------------------------
# Configurable Security Limits
# ------------------------------------------------------------------
REFERRAL_CODE_LENGTH = int(os.getenv("REFERRAL_CODE_LENGTH", "10"))
REFERRAL_CODE_ALPHABET = string.ascii_letters + string.digits
NEW_USER_WINDOW_MINUTES = int(os.getenv("NEW_USER_WINDOW_MINUTES", "30"))
REFERRAL_RATE_LIMIT_COUNT = int(os.getenv("REFERRAL_RATE_LIMIT_COUNT", "5"))

# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------




def generate_affiliate_code(length: int = REFERRAL_CODE_LENGTH) -> str:
    return ''.join(secrets.choice(REFERRAL_CODE_ALPHABET) for _ in range(length))


# ------------------------------------------------------------------
# Ensure every user has affiliate_code
# ------------------------------------------------------------------
def ensure_user_has_affiliate_code(user_id: int) -> str:
    try:
        with get_db_cursor(commit=True) as (cursor, _):
            cursor.execute(
                "SELECT affiliate_code FROM users WHERE user_id=%s FOR UPDATE",
                (user_id,),
            )
            row = cursor.fetchone()

            if row and row[0]:
                return row[0]

            # generate unique code
            for _ in range(5):
                code = generate_affiliate_code()
                cursor.execute(
                    "SELECT 1 FROM users WHERE affiliate_code=%s",
                    (code,),
                )
                if not cursor.fetchone():
                    cursor.execute(
                        "UPDATE users SET affiliate_code=%s WHERE user_id=%s",
                        (code, user_id),
                    )
                    log.info(f"[AFFILIATE] Code generated user={user_id}")
                    return code

            raise RuntimeError("Affiliate code generation failed")

    except Exception as e:
        log.error(f"[AFFILIATE] Code create error: {e}", exc_info=True)
        raise
