# dcst_mbot/delivery/telegram/forwarded/forwarded_message_handler.py
from pyrogram import Client, filters
from pyrogram.enums import ParseMode
from pyrogram.types import Message

from configs.logging_setup import log
from ....usecases.forwarded.save_forwarded_message_flow import (
    save_forwarded_message_flow,
)


def register_forwarded_message_handler(app: Client):

    @app.on_message(filters.command("start") & filters.private)
    async def start_handler(_: Client, message: Message):
        await message.reply_text("👋 Halo! Bot kelola siap menerima pesan forward.")

    @app.on_message(filters.forwarded & filters.private)
    async def handle_forwarded_message(_: Client, message: Message):
        try:
            inserted = await save_forwarded_message_flow(message)

            if inserted:
                await message.reply_text(
                    "✅ Data forward berhasil disimpan.",
                    parse_mode=ParseMode.HTML,
                )
            else:
                await message.reply_text(
                    "⚠️ Data sudah pernah disimpan.",
                    parse_mode=ParseMode.HTML,
                )

        except Exception:
            log.exception("[FORWARD] Handler error")
            await message.reply_text("❌ Terjadi kesalahan saat memproses pesan.")
