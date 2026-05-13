from pyrogram import Client
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from bots.drac1n_bot.repository.source_repository import search_sources_by_keyword
from common.utils.callback_helpers import safe_reply
from common.utils.request_state_manager import UserRequestStateManager


async def handle_autocomplete_source(client: Client, message: Message) -> bool:
    # Jangan tangani perintah (command)
    if message.text.startswith("/") and not message.text.startswith("/requestsource"):
        return False

    user_id = message.from_user.id
    state = UserRequestStateManager(user_id)

    if state.get_step() != "search_source_query":
        return False

    keyword = message.text.strip()
    results = search_sources_by_keyword(keyword)

    if not results:
        await safe_reply(message, "⚠️ Tidak ditemukan source yang cocok.")
        return True

    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(label, callback_data=f"request_source:{code}")]
            for code, label in results
        ]
        + [[InlineKeyboardButton("❌ Batal", callback_data="cancel_request_fsm")]]
    )

    await safe_reply(
        message,
        "🔍 Source yang mirip:",
        reply_markup=keyboard,
    )
    return True
