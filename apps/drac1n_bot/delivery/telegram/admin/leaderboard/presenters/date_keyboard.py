from datetime import date as date_cls
from calendar import monthrange
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from apps.drac1n_bot.delivery.telegram.admin.leaderboard.utils.timezone import today_wib


# ===============================
# DAY PICKER
# ===============================
def day_picker_keyboard(year_month: str) -> InlineKeyboardMarkup:
    """
    year_month: YYYY-MM
    Menampilkan tanggal valid pada bulan tersebut,
    maksimal sampai hari ini (WIB).
    """

    # Parse input defensively
    try:
        year, month = map(int, year_month.split("-"))
    except ValueError:
        # Fallback aman (bulan berjalan WIB)
        today = today_wib()
        year, month = today.year, today.month

    today = today_wib()
    last_day = monthrange(year, month)[1]

    buttons: list[InlineKeyboardButton] = []

    for day in range(1, last_day + 1):
        d = date_cls(year, month, day)

        # Jangan tampilkan tanggal di masa depan (WIB)
        if d > today:
            break

        buttons.append(
            InlineKeyboardButton(
                f"{day:02d}",
                callback_data=f"vip_date:select:{d.isoformat()}",
            )
        )

    # Grid 7 kolom (Senin–Minggu style UI)
    rows = [buttons[i : i + 7] for i in range(0, len(buttons), 7)]

    # Navigation
    rows.append(
        [
            InlineKeyboardButton(
                "⬅️ Kembali",
                callback_data=f"vip_date:month:{year:04d}-{month:02d}",
            )
        ]
    )

    return InlineKeyboardMarkup(rows)


# ===============================
# MONTH PICKER
# ===============================
def month_picker_keyboard(
    current_ym: str | None = None, max_back: int = 6
) -> InlineKeyboardMarkup:
    """
    Month picker keyboard.

    - current_ym : YYYY-MM (opsional, untuk posisi awal)
    - max_back   : jumlah bulan ke belakang (default 6)
    - Tidak menampilkan bulan di masa depan (WIB)
    """

    today = today_wib()

    # -----------------------------
    # Parse base month
    # -----------------------------
    if current_ym:
        try:
            year, month = map(int, current_ym.split("-"))
            base = date_cls(year, month, 1)
        except ValueError:
            base = date_cls(today.year, today.month, 1)
    else:
        base = date_cls(today.year, today.month, 1)

    buttons: list[InlineKeyboardButton] = []

    # -----------------------------
    # Generate months (WIB-safe)
    # -----------------------------
    for i in range(max_back):
        y = base.year
        m = base.month - i

        while m <= 0:
            y -= 1
            m += 12

        # Jangan tampilkan bulan di masa depan (WIB)
        if (y, m) > (today.year, today.month):
            continue

        label = date_cls(y, m, 1).strftime("%B %Y")

        buttons.append(
            InlineKeyboardButton(
                label,
                callback_data=f"vip_date:day:{y:04d}-{m:02d}",
            )
        )

    # -----------------------------
    # Layout (2 kolom)
    # -----------------------------
    rows = [buttons[i : i + 2] for i in range(0, len(buttons), 2)]

    # -----------------------------
    # Navigation
    # -----------------------------
    rows.append(
        [
            InlineKeyboardButton(
                "⬅️ Kembali",
                callback_data="vip_lb:daily:1",
            )
        ]
    )

    return InlineKeyboardMarkup(rows)
