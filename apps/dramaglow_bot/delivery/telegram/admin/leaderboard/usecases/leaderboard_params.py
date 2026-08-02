from dataclasses import dataclass
from datetime import datetime
from ..utils.timezone import today_wib

MAX_PAGE = 50


@dataclass
class LeaderboardParams:
    period: str
    page: int
    date: str | None


# ===============================
# INTERNAL: DATE NORMALIZER
# ===============================
def _normalize_daily_date(value: str | None) -> str:
    """
    Validasi & normalisasi tanggal harian (YYYY-MM-DD).
    Fallback ke hari ini (WIB).
    """
    if not value:
        return today_wib().isoformat()

    try:
        datetime.strptime(value, "%Y-%m-%d")
        return value
    except ValueError:
        return today_wib().isoformat()


# ===============================
# CALLBACK PARSER (FIXED)
# ===============================
def parse_leaderboard_callback(data: str) -> LeaderboardParams | None:
    """
    Parse callback data:
    vip_lb:{period}:{date}:{page}
    """

    try:
        parts = data.split(":")

        # ❌ Tolak format lama
        if len(parts) != 4:
            return None

        _, period, date_str, page_str = parts

        # page boundary-safe
        page = max(1, min(int(page_str), MAX_PAGE))

        # normalize date
        if date_str == "_" or period != "daily":
            date = None
        else:
            date = _normalize_daily_date(date_str)

        return LeaderboardParams(
            period=period,
            page=page,
            date=date,
        )

    except Exception:
        # Boundary function: silent fail
        return None
