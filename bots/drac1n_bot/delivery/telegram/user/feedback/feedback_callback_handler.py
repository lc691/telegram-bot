from pyrogram import Client
from pyrogram.types import CallbackQuery
from pyrogram.enums import ParseMode

from common.utils.admin_state_manager import AdminStateManager
from .....repository.feedback_repository import feedback_repository
from .feedback_routes import ROUTES


STATUS_LABELS = {
    "pending": "⏳ Menunggu Review",
    "resolved": "✅ Selesai",
    "rejected": "❌ Ditolak",
}


async def feedback_callback_handler(
    client: Client,
    callback_query: CallbackQuery
) -> bool:

    data = callback_query.data or ""

    # 1. filter layer
    if not data.startswith("feedback:"):
        return False

    if not callback_query.message:
        return True

    state = AdminStateManager(callback_query.from_user.id)

    # 2. resolve handler (FSM routing layer)
    handler = ROUTES.get(data)

    # 3. fallback safety
    if handler is None:
        await callback_query.answer(
            "Menu tidak dikenali",
            show_alert=True
        )
        return True

    # 4. single acknowledgment (ONLY ON SUCCESS PATH)
    await callback_query.answer()

    # 5. execute handler
    return await handler(state, callback_query)