from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from ..services.greeting import (
    get_country_code_by_language,
    get_greeting_by_country,
)
from .welcome import build_welcome_text
from shared.utils.menu_utils import edit_menu


async def show_main_menu(event, display_name: str = None):
    """
    MAIN MENU
    - single-message UI
    - EDIT ONLY (no reply, no send)
    """

    user = event.from_user
    if not user:
        return

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🔍 Cari Drama",
                    switch_inline_query_current_chat="",
                )
            ],
            [
                InlineKeyboardButton("📚 List Drama", url="https://t.me/dramaglow"),
                InlineKeyboardButton("💎 Beli VIP", callback_data="vip_buy:entry"),
            ],
            [
                InlineKeyboardButton("💰 Cuan 20%", callback_data="ref_menu"),
                InlineKeyboardButton("ℹ️ Info VIP", callback_data="vip_status"),
            ],
            [
                InlineKeyboardButton(
                    "💬 Grup Diskusi", url="https://t.me/+dumXicL9GcI3MGU9"
                ),
                InlineKeyboardButton("🆘 Hubungi Admin", url="https://t.me/mimindcstv"),
            ],
        ]
    )

    language_code = getattr(user, "language_code", "id")
    greeting = get_greeting_by_country(get_country_code_by_language(language_code))

    text = build_welcome_text(
        user_name=display_name or user.first_name or "User",
        greeting=greeting,
    )

    return await edit_menu(
        event=event,
        text=text,
        markup=keyboard,
    )
