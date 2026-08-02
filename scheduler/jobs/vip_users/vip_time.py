from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from dateutil import parser

from configs.logging_setup import log

from .constants import DEFAULT_TZ

_WIB = ZoneInfo(DEFAULT_TZ)


def now_wib() -> datetime:
    return datetime.now(_WIB)


def parse_datetime(value) -> datetime | None:
    """
    Parse datetime dari berbagai input.
    Pastikan hasilnya timezone-aware (WIB).
    """
    try:
        if isinstance(value, datetime):
            return value if value.tzinfo else value.replace(tzinfo=_WIB)

        if isinstance(value, str):
            dt = parser.parse(value)
            return dt if dt.tzinfo else dt.replace(tzinfo=_WIB)

    except Exception as e:
        log.warning("[VIP TIME] ⚠️ Gagal parse datetime: %s", e)

    return None


def calculate_vip_range(expired_at, total_days: int):
    """
    Hitung range VIP berdasarkan expired_at dan total hari.
    Digunakan hanya untuk tampilan (UI / caption).
    """
    expired_dt = parse_datetime(expired_at)
    if not expired_dt:
        return None, None

    start_dt = expired_dt - timedelta(days=total_days)
    return start_dt, expired_dt
