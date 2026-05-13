from pyrogram.enums import ParseMode
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from .message import (
    get_random_free_message,
    get_random_paid_message,
)


async def _reply_upgrade_free(message):
    return await message.reply_text(
        get_random_free_message(),
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "💎 Upgrade VIP",
                        url="https://t.me/dramaglow_bot?start=vip",
                    )
                ]
            ]
        ),
    )


async def _reply_upgrade_paid(message):
    return await message.reply_text(
        get_random_paid_message(),
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "🚀 Upgrade VIP",
                        url="https://t.me/dramaglow_bot?start=vip",
                    )
                ]
            ]
        ),
    )
