from pyrogram.enums import ParseMode
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from .status_text_presenter import format_status_text


def build_status_payload(context: dict):
    text = format_status_text(
        context["user_id"],
        context["status_data"],
        context["is_admin"],
        context["lang_code"],
    )

    buttons = [
        [
            InlineKeyboardButton(
                "💎 Beli VIP",
                callback_data="vip_buy:entry",
            )
        ],
    ]

    return {
        "text": text,
        "parse_mode": ParseMode.HTML,
        "disable_web_page_preview": True,
        "reply_markup": InlineKeyboardMarkup(buttons),
    }
