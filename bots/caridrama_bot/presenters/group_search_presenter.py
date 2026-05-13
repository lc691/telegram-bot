import re
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from .channel_validasi import is_valid_telegram_username

def build_result_keyboard(shows):
    buttons: list[list[InlineKeyboardButton]] = []
    row: list[InlineKeyboardButton] = []

    for show in shows:
        title = show.get("title")
        sid = show.get("id")
        message_id = show.get("message_id")
        channel_username = show.get("channel_username")

        if not title:
            continue

        label = f"🎬 {title}"
        if sid:
            label = f"{label} | ID: {sid}"

        # =============================
        # CASE 1 — LINK TELEGRAM VALID
        # =============================
        if (
            isinstance(message_id, int)
            and is_valid_telegram_username(channel_username)
        ):
            button = InlineKeyboardButton(
                label,
                url=f"https://t.me/{channel_username}/{message_id}",
            )

        # =============================
        # CASE 2 — FALLBACK (INLINE SEARCH)
        # =============================
        else:
            button = InlineKeyboardButton(
                label,
                switch_inline_query_current_chat=title,
            )

        row.append(button)

        if len(row) == 2:
            buttons.append(row)
            row = []

    if row:
        buttons.append(row)

    # =============================
    # GLOBAL ACTION BUTTON
    # =============================
    buttons.append(
        [
            InlineKeyboardButton(
                "🔍 Cari lagi",
                switch_inline_query_current_chat="",
            )
        ]
    )

    return InlineKeyboardMarkup(buttons)
