from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def build_voucher_keyboard():
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🎯 Klaim Sekarang",
                    switch_inline_query_current_chat="/redeem ",
                )
            ],
            [
                InlineKeyboardButton(
                    "💬 Tanya Admin",
                    url="https://t.me/mimindcstv",
                )
            ],
        ]
    )
