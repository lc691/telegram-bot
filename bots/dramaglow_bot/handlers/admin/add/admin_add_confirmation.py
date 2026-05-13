import re

from pyrogram import Client
from pyrogram.enums import ParseMode
from pyrogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from bots.dramaglow_bot.ui.dashboard import send_dashboard
from common.utils.admin_cache import admin_cache
from common.utils.admin_state_manager import AdminStateManager
from common.utils.state_helper import cancel_all_states
from configs.logging_setup import log


async def handle_admin_add_confirmation(
    app: Client, callback: CallbackQuery, state: AdminStateManager
):
    user_id = callback.from_user.id
    state = AdminStateManager(user_id)

    # STEP 1: Ambil data sementara dari state
    temp = state.get_temp_json("new_admin")
    if not temp:
        await callback.message.edit_text("❌ Data admin tidak ditemukan.")
        log.warning(f"[ADMIN_CONFIRM] Data sementara tidak ditemukan untuk {user_id}")
        return

    target_id = temp["user_id"]
    first_name = temp["first_name"]
    username = temp["username"]

    # STEP 2: Validasi callback pattern
    match = re.match(r"admin_add_confirm_(yes|no)_(\d+)", callback.data)
    if not match:
        await callback.message.edit_text("❌ Callback tidak valid.")
        log.warning(f"[ADMIN_CONFIRM] Format callback tidak cocok: {callback.data}")
        return

    action, confirm_target_id = match.groups()
    confirm_target_id = int(confirm_target_id)

    # STEP 3: Validasi kecocokan ID
    if confirm_target_id != target_id:
        await callback.message.edit_text("❌ Data tidak cocok atau sudah kadaluarsa.")
        cancel_all_states(user_id)
        log.warning(
            f"[ADMIN_CONFIRM] ID tidak cocok: {confirm_target_id} ≠ {target_id}"
        )
        return

    # STEP 4: Jika dibatalkan
    if action == "no":
        await callback.message.edit_text("❌ Penambahan admin dibatalkan.")
        cancel_all_states(user_id)
        log.info(f"[ADMIN_CONFIRM] Admin {user_id} membatalkan penambahan {target_id}")
        return

    # STEP 5: Insert ke database
    try:
        from db.admin.admin_manage import (  # Load di dalam agar dinamis saat testing
            add_admin_to_db,
        )

        success = add_admin_to_db(target_id, first_name, username)
        if success:
            admin_cache.add_admin(target_id)  # Tambahkan ke cache langsung
            await callback.message.edit_text(
                f"✅ Admin berhasil ditambahkan:\n\n"
                f"🆔 <code>{target_id}</code>\n"
                f"👤 {first_name}",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                "🔙 Kembali", callback_data="admin_tools_menu"
                            )
                        ]
                    ]
                ),
                parse_mode=ParseMode.HTML,
            )
            log.info(f"[ADMIN_CONFIRM] Admin baru ditambahkan: {target_id}")
            await send_dashboard(source=callback, is_callback=True)
        else:
            await callback.message.edit_text("⚠️ Admin sudah terdaftar sebelumnya.")
            log.info(f"[ADMIN_CONFIRM] Admin sudah ada: {target_id}")
    except Exception as e:
        log.exception(f"[ADMIN_CONFIRM] Gagal menambahkan admin: {e}")
        await callback.message.edit_text("⚠️ Gagal menambahkan admin ke database.")

    # STEP 6: Hapus state
    cancel_all_states(user_id)
    try:
        state.clear()
    except Exception as e:
        log.error(
            f"[ADMIN_CONFIRM] Gagal clear state user {user_id}: {e}", exc_info=True
        )
