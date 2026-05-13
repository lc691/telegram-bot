from math import ceil

from pyrogram.enums import ParseMode
from pyrogram.types import CallbackQuery

from bots.drac1n_bot.keyboard.admin_tools import generate_admin_list_markup
from configs.logging_setup import log
from db.admin.admin_query import get_all_admins

PER_PAGE = 5


async def show_admin_list_page(client, callback_query: CallbackQuery, page: int):
    """
    Tampilkan halaman `page` (dimulai dari 0) dari daftar admin.
    """
    try:
        admins = get_all_admins()
        total_admins = len(admins)

        if total_admins == 0:
            await callback_query.answer("⚠️ Belum ada admin terdaftar.", show_alert=True)
            log.warning("[ADMIN_PAGE] Tidak ada admin dalam daftar.")
            return

        total_pages = ceil(total_admins / PER_PAGE)
        page = max(0, min(page, total_pages - 1))  # Clamp page

        log.info(
            f"[ADMIN_PAGE] Menampilkan halaman {page + 1}/{total_pages} (total: {total_admins})"
        )

        markup = generate_admin_list_markup(admins, page=page, per_page=PER_PAGE)

        await callback_query.message.edit_text(
            f"👮‍♂️ <b>Daftar Admin (Halaman {page + 1}/{total_pages}):</b>",
            reply_markup=markup,
            parse_mode=ParseMode.HTML,
        )
        await callback_query.answer()

    except Exception as e:
        log.exception(f"[ADMIN_PAGE] Gagal menampilkan halaman ke-{page}: {e}")
        try:
            await callback_query.answer(
                "❌ Gagal memuat halaman admin.", show_alert=True
            )
        except Exception:
            pass


async def start_admin_page_callback(client, callback_query: CallbackQuery):
    """
    Dipicu oleh callback_data seperti `admin_page_2`.
    """
    try:
        page_str = callback_query.data.split("_")[-1]
        page = int(page_str)
        await show_admin_list_page(client, callback_query, page)

    except ValueError:
        log.warning(f"[ADMIN_PAGE] Format halaman tidak valid: {callback_query.data}")
        await callback_query.answer("❌ Format halaman salah.", show_alert=True)

    except Exception as e:
        log.exception(f"[ADMIN_PAGE] Error saat parsing halaman: {e}")
        await callback_query.answer("❌ Terjadi kesalahan internal.", show_alert=True)
