from math import ceil

from pyrogram.enums import ParseMode
from pyrogram.types import CallbackQuery

from bots.dramaglow_bot.keyboard.admin_tools import generate_admin_list_markup
from configs.logging_setup import log
from db.admin.admin_query import get_all_admins

PER_PAGE = 5


async def start_admin_list(client, callback_query: CallbackQuery, page: int = 0):
    log.info(f"[ADMIN_LIST] Diminta oleh user {callback_query.from_user.id}")

    try:
        # STEP 1: Ambil data admin
        admins = get_all_admins()
        total_admins = len(admins)
        if not admins:
            log.warning("[ADMIN_LIST] Tidak ada admin terdaftar.")
            await callback_query.answer(
                "⚠️ Tidak ada admin yang terdaftar.", show_alert=True
            )
            return

        # STEP 2: Hitung total halaman
        total_pages = max(1, ceil(total_admins / PER_PAGE))
        page = max(0, min(page, total_pages - 1))  # clamp page

        # STEP 3: Buat markup dan tampilkan
        markup = generate_admin_list_markup(admins, page=page, per_page=PER_PAGE)

        await callback_query.message.edit_text(
            f"👮‍♂️ <b>Daftar Admin (Halaman {page + 1}/{total_pages}):</b>",
            reply_markup=markup,
            parse_mode=ParseMode.HTML,
        )
        await callback_query.answer()
        log.info(
            f"[ADMIN_LIST] Menampilkan halaman {page + 1}/{total_pages} (total {total_admins} admin)."
        )

    except Exception as e:
        log.exception(f"[ADMIN_LIST] Gagal menampilkan daftar admin: {e}")
        try:
            await callback_query.answer(
                "❌ Gagal memuat daftar admin.", show_alert=True
            )
        except Exception as notify_err:
            log.warning(f"[ADMIN_LIST] Gagal kirim fallback alert: {notify_err}")


# === Wrapper untuk router
async def start_admin_list_callback(client, callback_query: CallbackQuery):
    await start_admin_list(client, callback_query, page=0)
