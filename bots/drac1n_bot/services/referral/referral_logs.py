import datetime

from configs.logging_setup import log
from db.connect import get_dict_cursor


def log_referral_event(referrer_user_id: int, referred_user_id: int, event_type: str):
    """
    Log aktivitas referral ke DB dan ke log file.
    
    Tabel: referral_logs (id, referrer_user_id, referred_user_id, event_type, created_at)
    """
    timestamp = datetime.datetime.utcnow()

    try:
        with get_dict_cursor(commit=True) as (cur, conn):
            cur.execute(
                """
                INSERT INTO referral_logs 
                (referrer_user_id, referred_user_id, event_type, created_at)
                VALUES (%s, %s, %s, %s)
                """,
                (referrer_user_id, referred_user_id, event_type, timestamp)
            )
            log.debug(f"[REFERRAL] Log disimpan ke DB: {event_type} | {referrer_user_id}->{referred_user_id}")
    except Exception as e:
        log.warning(f"[REFERRAL] Gagal menyimpan log ke DB: {e}")

    # Log ke file juga
    log.info(f"[REFERRAL_EVENT] {event_type} | referrer={referrer_user_id} referred={referred_user_id} at {timestamp}")
