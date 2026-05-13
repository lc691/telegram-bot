import re

from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

PER_PAGE = 5


def build_user_extend_markup(users, offset, source_bot):
    buttons = []

    for user in users:
        user_id = user.get("user_id")
        name = user.get("first_name") or "(Tanpa Nama)"
        username = f"@{user.get('username')}" if user.get("username") else "-"
        expired = user.get("end_date")
        expired_str = expired.strftime("%d %b %Y") if expired else "-"
        paket = user.get("paket") or "-"

        if len(name) > 30:
            name = name[:30] + "..."

        label = (
            f"🧑 {name} ({username})\n"
            f"📦 Paket: {paket}\n"
            f"📅 Expired: {expired_str}"
        )

        callback_data = f"vip_extend_user:{user_id}"

        buttons.append([InlineKeyboardButton(text=label, callback_data=callback_data)])

    nav_row = []
    if offset > 0:
        nav_row.append(
            InlineKeyboardButton(
                "◀️ Prev",
                callback_data=f"vip_extend_page:{offset - PER_PAGE}:{source_bot}",
            )
        )
    if len(users) == PER_PAGE:
        nav_row.append(
            InlineKeyboardButton(
                "Next ▶️",
                callback_data=f"vip_extend_page:{offset + PER_PAGE}:{source_bot}",
            )
        )
    if nav_row:
        buttons.append(nav_row)

    buttons.append(
        [InlineKeyboardButton("🔙 Kembali", callback_data=f"vip_tools:{source_bot}")]
    )

    return InlineKeyboardMarkup(buttons)
