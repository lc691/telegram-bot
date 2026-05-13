from __future__ import annotations

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

JAKARTA_TZ = ZoneInfo("Asia/Jakarta")


def ensure_aware(dt: datetime | None, tz=JAKARTA_TZ) -> datetime | None:
    """
    Pastikan datetime memiliki timezone (aware).
    Jika tidak, dianggap waktu UTC lalu dikonversi ke zona target.
    """
    if dt is None:
        return None

    # Jika naive (tidak punya timezone)
    if dt.tzinfo is None:
        # Anggap dari database itu UTC, lalu ubah ke WIB
        dt = dt.replace(tzinfo=timezone.utc).astimezone(tz)
    else:
        # Kalau sudah punya tz, langsung konversi ke zona target
        dt = dt.astimezone(tz)

    return dt


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)