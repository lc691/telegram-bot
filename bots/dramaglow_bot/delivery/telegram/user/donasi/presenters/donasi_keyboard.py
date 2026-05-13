from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def build_donasi_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("☕️ Trakteer", callback_data="donasi_trakteer"),
                InlineKeyboardButton("🍺 Pink", callback_data="donasi_pink"),
            ]
        ]
    )
