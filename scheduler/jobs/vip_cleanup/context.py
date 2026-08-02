from datetime import datetime, timezone
from zoneinfo import ZoneInfo

DEFAULT_TZ = "Asia/Jakarta"


def now_wib():
    return datetime.now(ZoneInfo(DEFAULT_TZ))


def now_utc():
    return datetime.now(timezone.utc)


def cron_context():
    return {
        "utc": now_utc(),
        "wib": now_wib(),
        "tz": DEFAULT_TZ,
    }
