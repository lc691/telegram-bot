from datetime import datetime, timezone
from typing import Optional
from zoneinfo import ZoneInfo
from config import DAILY_FREE_LIMIT

# =========================
# CONSTANTS
# =========================


TZ_ID = ZoneInfo("Asia/Jakarta")
TZ_MY = ZoneInfo("Asia/Kuala_Lumpur")


ACCESS_TEXT = {
    "id": {
        "reset": "🔄 Reset setiap jam 00:00 WIB",
        "upgrade": "⚠️ Untuk akses tanpa batas, upgrade ke VIP dengan /vip",
    },
    "ms": {
        "reset": "🔄 Reset setiap jam 00:00 Waktu Malaysia",
        "upgrade": "⚠️ Untuk akses tanpa batas, tingkatkan ke VIP dengan /vip",
    },
}


# =========================
# PURE HELPERS
# =========================


def _get_now() -> datetime:
    return datetime.now(timezone.utc)


def _progress_bar(value: int, max_value: int) -> str:
    value = min(value, max_value)
    return "🟩" * value + "⬜️" * (max_value - value)


def _get_access_count(
    last_access: Optional[datetime],
    access_today: int,
    now: datetime,
) -> int:
    if last_access and last_access.date() == now.date():
        return min(access_today, DAILY_FREE_LIMIT)
    return 0


def _get_lang_text(lang_code: str) -> dict:
    return ACCESS_TEXT.get(lang_code, ACCESS_TEXT["id"])


# =========================
# PUBLIC API
# =========================


def build_akses_harian(
    data: dict,
    is_admin: bool,
    lang_code: str = "id",
) -> str:
    """
    Render akses harian user non-VIP.
    """
    if is_admin:
        return "♾️ Admin (<b>Unlimited</b>)"

    if data.get("is_vip"):
        return "♾️ VIP (<b>Akses tak Terbatas</b>)"

    now = _get_now()

    count = _get_access_count(
        last_access=data.get("last_access"),
        access_today=data.get("access_today", 0),
        now=now,
    )

    progress = _progress_bar(count, DAILY_FREE_LIMIT)
    akses_line = f"{count}/{DAILY_FREE_LIMIT} {progress}"

    text = _get_lang_text(lang_code)

    return f"{akses_line}\n" f"{text['reset']}\n" f"{text['upgrade']}"
