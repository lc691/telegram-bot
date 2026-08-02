from pyrogram.enums import ParseMode
from pyrogram.types import CallbackQuery, Message

from apps.drac1n_bot.handlers.logic.markup_user_list import generate_user_list_keyboard
from apps.drac1n_bot.handlers.logic.parser_user_query import parse_query_params
from configs.logging_setup import log
from database.user_management import count_users, get_all_users, get_users


async def process_list_users(message: Message):
    try:
        users = get_all_users()
        if not users:
            await message.reply("Tidak ada data pengguna.")
            return

        text = generate_user_list_text(users)
        await message.reply(text, parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        log.exception(f"[LIST USERS] Error: {e}")
        await message.reply("❌ Terjadi kesalahan.")


async def process_list_users_callback(callback_query: CallbackQuery):
    try:
        params = parse_query_params(callback_query.data.removeprefix("list_users"))
        offset, limit = params.get("offset", 0), 5
        only_vip, search = params.get("vip", False), params.get("search", None)

        users = get_users(
            offset=offset, limit=limit, only_vip=only_vip, search_username=search
        )
        total = count_users(only_vip=only_vip, search_username=search)

        new_text = generate_user_list_text(users, offset)
        new_keyboard = generate_user_list_keyboard(
            offset, limit, total, only_vip, search
        )

        if (
            callback_query.message.text.strip() == new_text.strip()
            and callback_query.message.reply_markup == new_keyboard
        ):
            await callback_query.answer("ℹ️ Sudah di halaman ini.", show_alert=False)
            return

        await callback_query.message.edit_text(
            new_text, reply_markup=new_keyboard, parse_mode=ParseMode.MARKDOWN
        )

    except Exception as e:
        log.exception(f"[LIST USERS CALLBACK] Gagal: {e}")
        try:
            await callback_query.answer("❌ Gagal memuat daftar.")
        except Exception as ie:
            log.exception(f"[CALLBACK FALLBACK] {ie}")


def generate_user_list_text(users, offset=0):
    if not users:
        return "🚫 Tidak ada pengguna ditemukan."
    lines = [f"📋 **Daftar Pengguna** (Mulai dari #{offset + 1}):\n"]
    for i, user in enumerate(users, start=offset + 1):
        uid, name, uname, is_vip, expired = user
        tag = f"@{uname}" if uname else "-"
        status = "✅ VIP" if is_vip else "🆓 Free"
        exp = f" (sampai {expired.strftime('%Y-%m-%d')})" if expired else ""
        lines.append(f"**{i}.** `{uid}` — {name} ({tag})\n   {status}{exp}")
    return "\n".join(lines)
