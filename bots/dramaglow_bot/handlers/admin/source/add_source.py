from pyrogram import Client
from pyrogram.enums import ParseMode
from pyrogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from common.utils.admin_state_manager import AdminStateManager
from configs.logging_setup import log


async def admin_add_source_start(client: Client, callback_query: CallbackQuery):
    admin_id = callback_query.from_user.id
    state = AdminStateManager(admin_id)

    if state.has_active_step():
        await callback_query.answer("⚠️ Kamu sedang dalam proses lain.", show_alert=True)
        log.warning(
            f"[ADMIN_CALLBACK] Admin {admin_id} coba add source tapi FSM masih aktif."
        )
        return

    state.set_step("regular_step", "awaiting_source_code")
    await callback_query.message.edit_text(
        "✍️ Masukkan kode source baru (contoh: DCSTV):",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("❌ Batal", callback_data="request_menu")]]
        ),
        parse_mode=ParseMode.HTML,
    )
    log.info(
        f"[ADMIN_CALLBACK] Admin {admin_id} memulai add source (awaiting_source_code)."
    )

    return
