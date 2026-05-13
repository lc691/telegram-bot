from datetime import datetime, date as date_cls
from zoneinfo import ZoneInfo

# ===============================
# TIMEZONE CONSTANT
# ===============================
WIB = ZoneInfo("Asia/Jakarta")


# ===============================
# NOW / TODAY
# ===============================
def now_wib() -> datetime:
    """
    Current datetime in WIB (timezone-aware)
    """
    return datetime.now(WIB)


def today_wib() -> date_cls:
    """
    Current date in WIB
    """
    return now_wib().date()


# ===============================
# PARSING & FORMATTING
# ===============================
def parse_wib_date(date_str: str) -> date_cls:
    """
    Parse YYYY-MM-DD as WIB date
    """
    return datetime.strptime(date_str, "%Y-%m-%d").date()


def parse_wib_datetime(dt_str: str) -> datetime:
    """
    Parse ISO datetime and convert to WIB
    Accepts:
    - 2026-01-19T10:30:00Z
    - 2026-01-19 10:30:00
    """
    dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
    return dt.astimezone(WIB) if dt.tzinfo else dt.replace(tzinfo=WIB)


def format_wib_date(d: date_cls) -> str:
    """
    Format date to YYYY-MM-DD
    """
    return d.isoformat()


def format_wib_datetime(dt: datetime, fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    Format datetime as WIB
    """
    if dt.tzinfo:
        dt = dt.astimezone(WIB)
    else:
        dt = dt.replace(tzinfo=WIB)
    return dt.strftime(fmt)


# ===============================
# COMPARISON HELPERS
# ===============================
def is_today_wib(d: date_cls) -> bool:
    return d == today_wib()


def is_future_wib(d: date_cls) -> bool:
    return d > today_wib()


def is_past_wib(d: date_cls) -> bool:
    return d < today_wib()
