from pyrogram import Client
from pyrogram.types import CallbackQuery, Message

from bots.drac1n_bot.handlers.admin.broadcast.broadcast_cache import (
    get_broadcast_text,
)
from bots.drac1n_bot.handlers.admin.broadcast.sender import run_broadcast
from configs.logging_setup import log


def register_broadcast_callback(app: Client) -> None:
    # log.info("📡 Mendaftarkan handler callback tombol broadcast...")

    @app.on_callback_query()
    async def handle_broadcast_callbacks(
        client: Client,
        callback_query: CallbackQuery,
    ) -> None:
        user_id = callback_query.from_user.id
        data = callback_query.data or ""
        message: Message = callback_query.message

        if not data.startswith("broadcast_"):
            return

        action = data.split("_", 1)[1]

        log.info(
            "[CALLBACK] Tombol broadcast ditekan: %s oleh %s",
            data,
            user_id,
        )

        if action == "cancel":
            await message.delete()
            await callback_query.answer(
                "❌ Broadcast dibatalkan.",
                show_alert=True,
            )
            return

        if action == "confirm":
            broadcast_text = get_broadcast_text(user_id)

            if not broadcast_text:
                await callback_query.answer(
                    "⚠️ Tidak ada pesan broadcast yang tersimpan.",
                    show_alert=True,
                )
                return

            await callback_query.answer(
                "🚀 Broadcast dikirim...",
                show_alert=True,
            )

            await message.edit_text("📣 Sedang mengirim broadcast...")

            await run_broadcast(
                client,
                message,
                broadcast_text,
            )
