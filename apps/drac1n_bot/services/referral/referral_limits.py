# app/bots/drac1n_bot/referral/referral_limits.py

from datetime import datetime, timezone

from database.connection import get_db_cursor

# batas referral per window (misal 10 / jam)
REFERRAL_RATE_LIMIT = 10


# ---------------------------------------------------
# Window utils
# ---------------------------------------------------

def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _current_window() -> datetime:
    """
    Window = 1 jam (UTC)
    """
    now = _now_utc()
    return now.replace(minute=0, second=0, microsecond=0)


# ---------------------------------------------------
# Rate limit logic
# ---------------------------------------------------

def increment_referral_rate(referrer_user_id: int) -> int:
    """
    Tambah counter referral untuk referrer pada window saat ini
    """
    with get_db_cursor(commit=True) as (cursor, _):
        cursor.execute(
            """
            INSERT INTO referral_metrics (referrer_user_id, window_start, count)
            VALUES (%s, %s, 1)
            ON CONFLICT (referrer_user_id, window_start)
            DO UPDATE SET count = referral_metrics.count + 1
            RETURNING count
            """,
            (referrer_user_id, _current_window()),
        )
        return int(cursor.fetchone()[0])


def get_referral_rate(referrer_user_id: int) -> int:
    """
    Ambil jumlah referral pada window aktif
    """
    with get_db_cursor() as (cursor, _):
        cursor.execute(
            """
            SELECT count
            FROM referral_metrics
            WHERE referrer_user_id = %s
              AND window_start = %s
            """,
            (referrer_user_id, _current_window()),
        )
        row = cursor.fetchone()
        return int(row[0]) if row else 0


def is_referral_rate_limited(referrer_user_id: int) -> bool:
    """
    True jika sudah melewati batas
    """
    return get_referral_rate(referrer_user_id) >= REFERRAL_RATE_LIMIT
