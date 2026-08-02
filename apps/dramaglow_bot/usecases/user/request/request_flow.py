from pyrogram import Client
from pyrogram.types import Message

from shared.utils.request_state_manager import UserRequestStateManager


async def start_request_flow(client: Client, message: Message):
    user_id = message.from_user.id

    state = UserRequestStateManager(user_id)
    state.clear_all()
    state.set_step("awaiting_request_title")

    await message.reply_text(
        "📩 Silakan ketik judul film / series yang ingin kamu request:"
    )
