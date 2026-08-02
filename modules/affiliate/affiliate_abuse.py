from datetime import datetime, timezone

from configs.logging_setup import log
from database.connection import get_db_cursor


def log_abuse(user_id, referrer, event, reason, severity=1, meta=None):
    with get_db_cursor(commit=True) as (cur, _):
        cur.execute("""
            INSERT INTO affiliate_abuse_logs
            (user_id, referrer_user_id, event_type, reason, severity, metadata)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (user_id, referrer, event, reason, severity, meta))

    log.warning(f"[ABUSE] user={user_id} referrer={referrer} event={event} reason={reason}")


def detect_self_referral(user_id):
    with get_db_cursor() as (cur, _):
        cur.execute("""
            SELECT referrer_user_id FROM users
            WHERE user_id = %s
        """, (user_id,))
        row = cur.fetchone()

    if not row or not row[0]:
        return False, None

    referrer = row[0]

    if referrer == user_id:
        log_abuse(user_id, referrer, "SELF_REFERRAL", "User referred themselves", 3)
        return True, referrer

    return False, referrer


def detect_burst_referral(referrer):
    if not referrer:
        return False

    with get_db_cursor() as (cur, _):
        cur.execute("""
            SELECT COUNT(*)
            FROM users
            WHERE referrer_user_id = %s
              AND created_at > NOW() - INTERVAL '10 minutes'
        """, (referrer,))
        count = cur.fetchone()[0]

    if count >= 5:
        log_abuse(referrer, referrer, "BURST_REFERRAL", f"{count} akun dalam 10 menit", 2)
        return True

    return False
