from datetime import datetime, timedelta, date as date_cls
from zoneinfo import ZoneInfo
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from apps.drac1n_bot.delivery.telegram.user.common.konstanta import MAX_PAGE

# ===============================
# TIMEZONE
# ===============================
WIB = ZoneInfo("Asia/Jakarta")


def today_wib() -> date_cls:
    return datetime.now(WIB).date()


def leaderboard_keyboard(*, period: str, page: int, date: str | None):
    """
    Build keyboard leaderboard VIP.
    UI only, tanpa I/O dan tanpa logging.
    """

    rows: list[list[InlineKeyboardButton]] = []

    # ===============================
    # PERIOD SWITCH (FIXED)
    # ===============================
    rows.append(
        [
            InlineKeyboardButton(
                "🔥 Harian" + (" ✅" if period == "daily" else ""),
                "vip_lb:daily:_:1",
            ),
            InlineKeyboardButton(
                "📆 Mingguan" + (" ✅" if period == "weekly" else ""),
                "vip_lb:weekly:_:1",
            ),
        ]
    )
    rows.append(
        [
            InlineKeyboardButton(
                "📅 Bulanan" + (" ✅" if period == "monthly" else ""),
                "vip_lb:monthly:_:1",
            ),
            InlineKeyboardButton(
                "🏆 All" + (" ✅" if period == "all" else ""),
                "vip_lb:all:_:1",
            ),
        ]
    )

    # ===============================
    # DAILY NAVIGATION (SUDAH BENAR)
    # ===============================
    if period == "daily" and date:
        try:
            current = datetime.strptime(date, "%Y-%m-%d").date()
        except ValueError:
            current = today_wib()

        prev_date = (current - timedelta(days=1)).isoformat()

        row = [
            InlineKeyboardButton(
                "⏮ Sebelumnya",
                f"vip_lb:daily:{prev_date}:{page}",
            ),
            InlineKeyboardButton(
                "📅 Pilih Tanggal",
                f"vip_date:month:{current:%Y-%m}",
            ),
        ]

        if current < today_wib():
            next_date = (current + timedelta(days=1)).isoformat()
            row.append(
                InlineKeyboardButton(
                    "⏭ Berikutnya",
                    f"vip_lb:daily:{next_date}:{page}",
                )
            )

        rows.append(row)

    # ===============================
    # PAGINATION (FIXED)
    # ===============================
    nav: list[InlineKeyboardButton] = []

    safe_date = date if date else "_"

    if page > 1:
        nav.append(
            InlineKeyboardButton(
                text="⬅️ Prev",
                callback_data=f"vip_lb:{period}:{safe_date}:{page - 1}",
            )
        )

    if page < MAX_PAGE:
        nav.append(
            InlineKeyboardButton(
                text="Next ➡️",
                callback_data=f"vip_lb:{period}:{safe_date}:{page + 1}",
            )
        )

    if nav:
        rows.append(nav)

    # ===============================
    # CLOSE
    # ===============================
    rows.append([InlineKeyboardButton("🚪 Tutup", "close")])

    return InlineKeyboardMarkup(rows)
