from pyrogram import Client, filters
from pyrogram.enums import ParseMode
from pyrogram.types import Message

from bots.dramaglow_bot.decorators.admin_only import admin_only
from configs.logging_setup import log

from .preview import preview_broadcast


def register_broadcast_message_handlers(app: Client):
    # log.info("🔔 Memasang handler /broadcast...")

    @app.on_message(filters.command("broadcast") & filters.private, group=0)
    @admin_only()
    async def handle_broadcast_command(client: Client, message: Message):
        user_id = message.from_user.id
        log.info(f"🔥 /broadcast dipanggil oleh user_id: {user_id}")

        try:
            # Cek apakah ada isi broadcast
            if len(message.command) < 2:
                log.warning("⚠️ Tidak ada isi broadcast.")
                await message.reply_text(
                    "⚠️ Mohon sertakan isi pesan broadcast.\n\n"
                    "Contoh: `/broadcast Halo semua!`",
                    quote=True,
                )
                return

            # Ambil teks broadcast
            broadcast_text = message.text.split(" ", 1)[1]
            log.info(f"💬 Teks broadcast: {broadcast_text}")

            # Kirim preview broadcast dengan format HTML
            await preview_broadcast(client, message, broadcast_text)

            log.info("✅ Preview broadcast berhasil dikirim.")

        except Exception as e:
            log.exception(f"❌ Error saat handle /broadcast oleh {user_id}")
            await message.reply_text(
                "⚠️ Terjadi error internal saat memproses broadcast.",
                quote=True,
                parse_mode=ParseMode.HTML,
            )
