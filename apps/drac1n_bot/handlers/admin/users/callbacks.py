from urllib.parse import parse_qs

from pyrogram import filters
from pyrogram.enums import ParseMode
from pyrogram.errors import MessageNotModified
from pyrogram.handlers import CallbackQueryHandler
from pyrogram.types import CallbackQuery

from shared.utils.admin_cache import admin_cache
from configs.logging_setup import log
from database.user_management import count_users, get_users

from .components import generate_user_list_keyboard, generate_user_list_text


async def list_users_callback(client, callback_query: CallbackQuery):
    if not await admin_cache.is_admin_async(callback_query.from_user.id):
        await callback_query.answer("🚫 Anda tidak diizinkan.", show_alert=True)
        return

    try:
        query_data = callback_query.data.removeprefix("list_users")
        params = parse_query_params(query_data)

        source = params.get("source", "drac1n")
        offset = params.get("offset", 0)
        limit = 5
        only_vip = params.get("vip", False)
        search = params.get("search", None)

        users = get_users(
            offset=offset,
            limit=limit,
            only_vip=only_vip,
            search_username=search,
            source=source,
        )
        total = count_users(only_vip=only_vip, search_username=search, source=source)

        new_text = generate_user_list_text(users, offset, total, source)
        new_keyboard = generate_user_list_keyboard(
            offset, limit, total, only_vip, search, source
        )

        if (callback_query.message.text or "").strip() == new_text.strip() and str(
            callback_query.message.reply_markup
        ) == str(new_keyboard):
            await callback_query.answer("ℹ️ Sudah di halaman ini.", show_alert=False)
            return

        await callback_query.message.edit_text(
            new_text,
            reply_markup=new_keyboard,
            parse_mode=ParseMode.HTML,
        )

    except MessageNotModified:
        await callback_query.answer("ℹ️ Tidak ada perubahan.")
    except Exception as e:
        log.exception(f"[LIST USERS CALLBACK] Gagal memproses callback: {e}")
        try:
            await callback_query.answer("❌ Gagal memuat daftar pengguna.")
        except Exception as inner_e:
            log.exception(f"[LIST USERS CALLBACK] Gagal fallback edit: {inner_e}")


def parse_query_params(raw_query: str):
    if not raw_query:
        return {}
    parsed = parse_qs(raw_query.strip("?"))
    return {
        "offset": max(0, int(parsed.get("offset", [0])[0])),
        "vip": parsed.get("vip", ["false"])[0].lower() == "true",
        "search": parsed.get("search", [None])[0],
        "source": parsed.get("source", ["drac1n"])[0],
    }


# ✅ Ini handler-nya yang akan didaftarkan
list_users_callback_handler = CallbackQueryHandler(
    callback=list_users_callback,
    filters=filters.regex(r"^list_users(\?[^ ]*)?$"),
)
