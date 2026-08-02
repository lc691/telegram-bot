from datetime import datetime
from zoneinfo import ZoneInfo


def format_wib(dt):
    if not dt:
        return "-"
    if isinstance(dt, str):
        try:
            dt = datetime.fromisoformat(dt)
        except Exception:
            return "-"
    return dt.astimezone(
        ZoneInfo("Asia/Jakarta")
    ).strftime("%d-%m-%Y %H:%M WIB")


def sisa_waktu(expired):
    if not expired:
        return "-"
    if isinstance(expired, str):
        try:
            expired = datetime.fromisoformat(expired)
        except Exception:
            return "-"
    now = datetime.now(ZoneInfo("Asia/Jakarta"))
    delta = expired - now
    if delta.total_seconds() <= 0:
        return "Habis"
    return f"{delta.days} hari {delta.seconds // 3600} jam"
