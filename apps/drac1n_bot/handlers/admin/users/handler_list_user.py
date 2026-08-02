from pyrogram import filters
from pyrogram.enums import ParseMode
from pyrogram.types import Message

from shared.utils.admin_cache import admin_cache
from configs.logging_setup import log
from database.user_management import get_all_users


def register_list_user_handlers(app):
    from .callbacks import list_users_callback_handler

    app.add_handler(list_users_callback_handler)

    @app.on_message(filters.command("list_users"))
    async def list_users_handler(client, message: Message):
        if not await admin_cache.is_admin_async(message.from_user.id):
            await message.reply("🚫 Anda tidak memiliki akses.")
            return

        try:
            users = get_all_users()

            if not users:
                await message.reply("Tidak ada data pengguna.")
                return

            lines = ["📋 **Daftar Pengguna Terdaftar:**\n"]
            for i, user in enumerate(users, start=1):
                uid, name, uname, is_vip, expired = user
                tag = f"@{uname}" if uname else "-"
                status = "✅ VIP" if is_vip else "🆓 Free"
                exp = f" (sampai {expired.strftime('%Y-%m-%d')})" if expired else ""
                lines.append(f"**{i}.** {uid} — {name} ({tag})\n   {status}{exp}")

            await message.reply("\n".join(lines), parse_mode=ParseMode.MARKDOWN)

        except Exception as e:
            log.exception(f"[LIST USERS] Gagal memproses perintah /list_users: {e}")
            await message.reply("❌ Terjadi kesalahan saat mengambil data.")
