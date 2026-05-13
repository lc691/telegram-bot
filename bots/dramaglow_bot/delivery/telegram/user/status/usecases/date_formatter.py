from datetime import datetime, timezone
from typing import Optional

import pytz

from .timzone_map import TIMEZONE_MAP


def format_date(
    dt: Optional[datetime],
    lang_code: str = "id",
    fmt: str = "%d %b %Y %H:%M",
) -> str:
    """
    Format UTC datetime ke local timezone sesuai bahasa.
    """
    if dt is None:
        return "—"

    # Pastikan datetime aware (fallback aman)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    tz_name, label = TIMEZONE_MAP.get(
        lang_code,
        TIMEZONE_MAP["id"],
    )

    local_tz = pytz.timezone(tz_name)
    local_dt = dt.astimezone(local_tz)

    return f"{local_dt.strftime(fmt)} ({label})"
