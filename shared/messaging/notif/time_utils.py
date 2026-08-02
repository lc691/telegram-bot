from datetime import datetime, timezone
from zoneinfo import ZoneInfo


def format_wib(dt: datetime | None) -> str:
    """Format datetime ke tampilan lokal WIB yang ramah pengguna."""
    if not dt:
        return "-"
    # Pastikan datetime timezone-aware
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    # Konversi ke WIB dan format
    return dt.astimezone(ZoneInfo("Asia/Jakarta")).strftime("%d %B %Y %H:%M WIB")
