# anti_abuse_referral.py
# FINAL – Referral Anti-Abuse System (Rule-based + Scoring)

from datetime import datetime, timezone

from configs.logging_setup import log
from db.connect import get_db_cursor


# ========================================================================
# CONFIG
# ========================================================================

# Score threshold untuk HARD BLOCK
ABUSE_BLOCK_THRESHOLD = 100

# ========================================================================
# RULES
# Each rule returns: (is_suspicious: bool, reason: str | None, score: int)
# ========================================================================


# RULE 1 — Self referral (HARD SIGNAL)
# ========================================================================
def rule_self_referral(user_id: int, referrer_id: int):
    if user_id == referrer_id:
        return True, "self_referral", 100
    return False, None, 0


# RULE 2 — Account too new (< 2 minutes)
# Soft signal (avoid false positive)
# ========================================================================
def rule_account_too_new(user_id: int):
    with get_db_cursor() as (cursor, _):
        cursor.execute(
            "SELECT created_at FROM users WHERE user_id = %s",
            (user_id,),
        )
        row = cursor.fetchone()
        if not row or not row[0]:
            return False, None, 0

        age_seconds = (datetime.now(timezone.utc) - row[0]).total_seconds()
        if age_seconds < 120:
            return True, "account_too_new", 30

    return False, None, 0


# RULE 3 — Burst referrals from same referrer (10 minutes)
# Strong but not absolute
# ========================================================================
def rule_burst_referrals(referrer_id: int):
    with get_db_cursor() as (cursor, _):
        cursor.execute(
            """
            SELECT COUNT(*)
            FROM users
            WHERE referrer_user_id = %s
              AND created_at > NOW() - INTERVAL '10 minutes'
            """,
            (referrer_id,),
        )
        count = cursor.fetchone()[0]

        if count >= 5:
            return True, "burst_referrals_10min", 50

    return False, None, 0


# RULE 4 — Same IP used by multiple accounts
# Softened for mobile/NAT environment
# ========================================================================
def rule_same_ip(user_id: int):
    with get_db_cursor() as (cursor, _):
        cursor.execute(
            "SELECT last_ip FROM users WHERE user_id = %s",
            (user_id,),
        )
        row = cursor.fetchone()
        if not row or not row[0]:
            return False, None, 0

        ip = row[0]

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM users
            WHERE last_ip = %s
              AND user_id != %s
            """,
            (ip, user_id),
        )
        count = cursor.fetchone()[0]

        if count >= 3:
            return True, "same_ip_multiple_accounts", 40

    return False, None, 0


# RULE 5 — Suspicious purchase / commission pattern
# Very soft signal, informational
# ========================================================================
def rule_fake_purchase_pattern(user_id: int):
    with get_db_cursor() as (cursor, _):
        cursor.execute(
            """
            SELECT COUNT(*)
            FROM affiliate_commission_logs
            WHERE referred_user_id = %s
            """,
            (user_id,),
        )
        count = cursor.fetchone()[0]

        if count >= 3:
            return True, "suspicious_commission_pattern", 30

    return False, None, 0


# ========================================================================
# AGGREGATOR
# ========================================================================
def evaluate_referral_abuse_rules(user_id: int, referrer_id: int):
    reasons: list[str] = []
    score = 0

    for rule in (
        lambda: rule_self_referral(user_id, referrer_id),
        lambda: rule_account_too_new(user_id),
        lambda: rule_burst_referrals(referrer_id),
        lambda: rule_same_ip(user_id),
        lambda: rule_fake_purchase_pattern(user_id),
    ):
        suspicious, reason, sc = rule()
        if suspicious:
            reasons.append(reason)
            score += sc

    return reasons, score


# ========================================================================
# ENTRY POINT (USED BY handle_referral_assignment)
# ========================================================================
def check_and_flag_referral_abuse(user_id: int, referrer_id: int) -> bool:
    """
    Returns:
        True  -> HARD BLOCK referral
        False -> Allow referral (may still be logged as suspicious)
    """

    try:
        reasons, score = evaluate_referral_abuse_rules(user_id, referrer_id)

        if not reasons:
            return False  # Clean

        # HARD BLOCK
        if score >= ABUSE_BLOCK_THRESHOLD:
            with get_db_cursor(commit=True) as (cursor, _):
                cursor.execute(
                    """
                    UPDATE users
                    SET
                        abuse_flag = TRUE,
                        abuse_reason = %s,
                        abuse_score = %s
                    WHERE user_id = %s
                    """,
                    (
                        ",".join(reasons),
                        score,
                        user_id,
                    ),
                )

            log.warning(
                "[REFERRAL-ABUSE] HARD BLOCK user=%s referrer=%s score=%s reasons=%s",
                user_id,
                referrer_id,
                score,
                reasons,
            )
            return True

        # SOFT FLAG (log only)
        log.info(
            "[REFERRAL-ABUSE] Soft signal user=%s referrer=%s score=%s reasons=%s",
            user_id,
            referrer_id,
            score,
            reasons,
        )
        return False

    except Exception:
        log.exception(
            "[REFERRAL-ABUSE] Fatal error user=%s referrer=%s",
            user_id,
            referrer_id,
        )
        return False
