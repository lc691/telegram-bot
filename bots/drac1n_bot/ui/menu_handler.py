from pyrogram.enums import ParseMode
from pyrogram.errors import MessageNotModified
from pyrogram.types import CallbackQuery

from bots.drac1n_bot.constants.menu_definitions import menus
from common.utils.admin_cache import admin_cache
from common.utils.callback_helpers import safe_answer, safe_edit_text
from configs.logging_setup import log


async def handle_dynamic_menu(callback_query: CallbackQuery):
    """
    Menangani semua menu dinamis berdasarkan callback_data yang cocok dengan entri di 'menus'.
    """
    user_id = callback_query.from_user.id
    callback_data = callback_query.data

    try:
        # ✅ Cek izin akses admin untuk menu tertentu
        admin_menus = {"admin_tools_menu", "vip_tools_menu", "channel_menu"}
        if callback_data in admin_menus and not admin_cache.is_admin(user_id):
            log.warning(
                f"[MENU_ACCESS_DENIED] User {user_id} mencoba akses '{callback_data}' tanpa izin."
            )
            await safe_answer(callback_query, "⛔️ Anda bukan admin!", show_alert=True)
            return

        # ✅ Ambil definisi menu dari dictionary
        menu = menus.get(callback_data)
        if not menu:
            log.warning(f"[MENU_NOT_FOUND] Menu '{callback_data}' tidak ditemukan.")
            await safe_answer(
                callback_query, "⚠️ Menu tidak ditemukan.", show_alert=True
            )
            return

        # ✅ Perbarui UI dengan teks dan tombol baru
        await safe_edit_text(
            callback_query.message,
            new_text=menu["title"],
            reply_markup=menu["markup"](),
            parse_mode=ParseMode.HTML,
        )

        await safe_answer(callback_query, "✅ Menu diperbarui")

    except MessageNotModified:
        log.debug(f"[MENU_NO_CHANGE] Tidak ada perubahan pada '{callback_data}'")
        await safe_answer(callback_query, "✅ Tidak ada perubahan")

    except Exception as e:
        log.exception(f"[MENU_ERROR] Gagal memproses menu '{callback_data}': {e}")
        await safe_answer(callback_query, "❌ Gagal menampilkan menu.", show_alert=True)
