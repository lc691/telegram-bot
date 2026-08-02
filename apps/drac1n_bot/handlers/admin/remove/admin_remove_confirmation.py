import re

from pyrogram import Client
from pyrogram.enums import ParseMode
from pyrogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from apps.drac1n_bot.ui.dashboard import send_dashboard
from shared.utils.admin_cache import admin_cache
from shared.utils.admin_state_manager import AdminStateManager
from shared.utils.state_helper import cancel_all_states
from configs.logging_setup import log


async def handle_admin_remove_confirmation(
    client: Client, callback: CallbackQuery, state
):
    user_id = callback.from_user.id
    log.info(
        f"[ADMIN_REMOVE_CONFIRM] Callback diterima dari user {user_id}: {callback.data}"
    )

    try:
        state = AdminStateManager(user_id)
        temp = state.get_temp_json("remove_admin")
        if not temp:
            log.warning("[ADMIN_REMOVE_CONFIRM] Data state sementara kosong.")
            await callback.message.edit_text("❌ Data tidak ditemukan.")
            return

        # STEP 1: Ambil data dari state
        target_id = temp.get("user_id")
        first_name = temp.get("first_name", "-")
        username = temp.get("username", "-")

        log.info(
            f"[ADMIN_REMOVE_CONFIRM] Target: {target_id} — {first_name} (@{username})"
        )

        # STEP 2: Validasi format callback
        match = re.match(r"admin_remove_confirm_(yes|no)_(\d+)", callback.data)
        if not match:
            log.warning("[ADMIN_REMOVE_CONFIRM] Format callback tidak valid.")
            await callback.message.edit_text("❌ Format konfirmasi tidak dikenali.")
            return

        action, confirm_target_id = match.groups()
        confirm_target_id = int(confirm_target_id)

        # STEP 3: Validasi ID sesuai
        if confirm_target_id != target_id:
            log.warning("[ADMIN_REMOVE_CONFIRM] ID target tidak cocok dengan state.")
            await callback.message.edit_text(
                "❌ Data tidak cocok atau sudah kadaluarsa."
            )
            cancel_all_states(user_id)
            return

        # STEP 4: Jika dibatalkan
        if action == "no":
            await callback.message.edit_text("❌ Penghapusan admin dibatalkan.")
            log.info(f"[ADMIN_REMOVE_CONFIRM] Admin {user_id} membatalkan penghapusan.")
            cancel_all_states(user_id)
            return

        # STEP 5: Hapus admin dari database
        log.info(f"[ADMIN_REMOVE_CONFIRM] Menghapus admin {target_id} dari database...")
        from database.repositories.admin.admin_manage import remove_admin_from_db

        success = remove_admin_from_db(target_id)
        if success:
            log.info(
                f"[ADMIN_REMOVE_CONFIRM] Admin {target_id} berhasil dihapus dari DB."
            )

            # STEP 6: Hapus dari cache jika ada
            if hasattr(admin_cache, "remove_admin"):
                admin_cache.remove_admin(target_id)
                log.info(
                    f"[ADMIN_REMOVE_CONFIRM] Admin {target_id} dihapus dari cache."
                )
            else:
                log.warning("[ADMIN_CACHE] Method remove_admin tidak tersedia.")

            await callback.message.edit_text(
                f"✅ Admin berhasil dihapus:\n\n🆔 `{target_id}`\n👤 {first_name}",
                log.warninglineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                "🔙 Kembali", callback_data="admin_list_start"
                            )
                        ]
                    ]
                ),
                parse_mode=ParseMode.HTML,
            )
            await send_dashboard(source=callback, is_callback=True)
        else:
            log.warning(
                f"[ADMIN_REMOVE_CONFIRM] Admin {target_id} tidak ditemukan di DB."
            )
            await callback.message.edit_text(
                "⚠️ Admin tidak ditemukan atau sudah dihapus."
            )

    except Exception as e:
        log.exception(f"[ADMIN_REMOVE_CONFIRM] Error saat proses: {e}")
        try:
            await callback.message.edit_text("⚠️ Gagal menghapus admin dari database.")
        except Exception as e2:
            log.warning(f"[ADMIN_REMOVE_CONFIRM] Gagal kirim fallback: {e2}")

    # STEP 7: Clear state
    try:
        cancel_all_states(user_id)
        state.clear()
        log.info(f"[ADMIN_REMOVE_CONFIRM] State dibersihkan untuk {user_id}")
    except Exception as e:
        log.error(
            f"[ADMIN_REMOVE_CONFIRM] Gagal membersihkan state: {e}", exc_info=True
        )
