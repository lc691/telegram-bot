# ================================================
#  ANTI-ABUSE DETECTOR
# ================================================

from datetime import datetime, timedelta

from configs.logging_setup import log
from db.connect import get_db_cursor


def check_affiliate_abuse(user_id: int) -> dict:
    """
    Memeriksa apakah user melakukan pelanggaran affiliate.
    Bila abuse terdeteksi → auto-flag user.
    """

    abuse_reasons = []

    with get_db_cursor(commit=True) as (cursor, conn):

        # ---------------------------------------------------------
        # RULE 1: Multi-account yang memakai upline sama + device sama
        # ---------------------------------------------------------
        cursor.execute("""
            SELECT device_id, referrer_user_id
            FROM users
            WHERE user_id = %s
        """, (user_id,))
        row = cursor.fetchone()

        if not row:
            return {"abuse": False}

        device_id, referrer = row

        if device_id and referrer:
            cursor.execute("""
                SELECT COUNT(*)
                FROM users
                WHERE device_id = %s
                AND referrer_user_id = %s
                AND user_id != %s
            """, (device_id, referrer, user_id))
            (cnt,) = cursor.fetchone()

            if cnt >= 2:
                abuse_reasons.append("multi-account-suspicious")

        # ---------------------------------------------------------
        # RULE 2: Pembelian beruntun abnormal (spam)
        # ---------------------------------------------------------
        cursor.execute("""
            SELECT created_at
            FROM vip_users
            WHERE user_id = %s
            ORDER BY created_at DESC
            LIMIT 2
        """, (user_id,))
        rows = cursor.fetchall()

        if len(rows) >= 2:
            last_tx = rows[0][0]
            before_last_tx = rows[1][0]
            diff = last_tx - before_last_tx

            # Contoh threshold
            if diff.total_seconds() < 120:  # < 2 menit beli berulang
                abuse_reasons.append("rapid-purchase-pattern")

        # ---------------------------------------------------------
        # RULE 3: Referral chain abnormal (1 user refer > 200)
        # ---------------------------------------------------------
        cursor.execute("""
            SELECT referral_count
            FROM users
            WHERE user_id = %s
        """, (referrer,))
        row = cursor.fetchone()
        if row:
            (ref_count,) = row

            if ref_count > 200:
                abuse_reasons.append("mass-referral-abnormal")

        # ---------------------------------------------------------
        # RULE 4: Self-referral (user A refer user A)
        # ---------------------------------------------------------
        if referrer == user_id and referrer is not None:
            abuse_reasons.append("self-referral")

        # ---------------------------------------------------------
        # APPLY FLAG IF NEEDED
        # ---------------------------------------------------------
        if abuse_reasons:
            cursor.execute("""
                UPDATE users
                SET abuse_flag = TRUE,
                    abuse_reason = %s
                WHERE user_id = %s
            """, (", ".join(abuse_reasons), user_id))

            log.warning(
                f"[AFFILIATE_ABUSE] user {user_id} flagged: {abuse_reasons}"
            )

            return {
                "abuse": True,
                "reasons": abuse_reasons
            }

    return {"abuse": False}


def is_user_flagged(user_id: int) -> bool:
    """ Cek apakah user sudah dalam daftar hitam affiliate """
    with get_db_cursor() as (cursor, conn):
        cursor.execute("""
            SELECT abuse_flag FROM users
            WHERE user_id = %s
        """, (user_id,))
        row = cursor.fetchone()
        return row[0] if row else False
