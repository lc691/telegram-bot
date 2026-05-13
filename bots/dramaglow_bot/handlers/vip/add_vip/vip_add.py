from pyrogram import Client
from pyrogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from common.bot_utils import get_clean_bot_key
from common.utils.admin_cache import admin_cache
from common.utils.admin_notifier import notify_admin_error
from common.utils.callback_helpers import safe_answer, safe_edit_text
from common.utils.fsm_helpers import validate_no_conflict
from common.utils.vip_state_manager import VipStateManager
from configs.logging_setup import log


async def vip_add_start(client: Client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    bot_name = getattr(client, "bot_name", client.name)

    log.info(
        f"[VIP_ADD_START] 🚀 Dimulai oleh admin user_id={user_id} di bot={bot_name}"
    )

    # Validasi admin
    if not await admin_cache.is_admin_async(user_id):
        log.warning(
            f"[VIP_ADD_START] 🚫 Non-admin {user_id} mencoba akses di bot={bot_name}"
        )
        await safe_answer(
            callback_query,
            "🚫 Anda tidak diizinkan menggunakan fitur ini.",
            show_alert=True,
        )
        return

    state = VipStateManager(user_id, source_bot=bot_name)

    try:
        # Cek FSM aktif → jika ya, clear
        conflict_resolved = await validate_no_conflict(user_id, state, callback_query)

        # 🧠 Setelah clear, atau tidak ada konflik, langsung mulai FSM baru
        state.clear()
        state.set_temp("source_bot", bot_name)
        state.set_vip_add_step("vip_add:ask_user_id")

        await safe_answer(callback_query, "📝 Masukkan user_id pengguna VIP")

        message_text = (
            "📥 Silakan masukkan **user_id** pengguna yang ingin dijadikan VIP.\n\n"
            "📝 Pastikan user tersebut sudah memulai bot ini terlebih dahulu."
        )
        markup = InlineKeyboardMarkup(
            [[InlineKeyboardButton("❌ Batal", callback_data=f"vip_tools:{bot_name}")]]
        )

        await safe_edit_text(callback_query.message, message_text, reply_markup=markup)

    except Exception as e:
        log.error(f"[VIP_ADD_START] ❌ Gagal: {e}", exc_info=True)
        await notify_admin_error(
            client, f"[VIP_ADD_START] ❌ Error user_id={user_id} di bot={bot_name}: {e}"
        )
        await safe_answer(
            callback_query, "❌ Gagal memulai proses VIP.", show_alert=True
        )
