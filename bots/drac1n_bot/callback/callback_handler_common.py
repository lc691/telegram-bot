# file: bots/drac1n_bot/callback/callback_handler_common.py

from pyrogram import Client, filters
from pyrogram.types import CallbackQuery

from configs.logging_setup import log


def register_common_callbacks(app: Client):
    @app.on_callback_query(filters.regex(r"^back_to_home$"), group=3)
    async def back_to_home(client: Client, callback_query: CallbackQuery):
        log.info("[CB] back_to_home ditekan")
        await callback_query.answer("🔙 Kembali ke menu utama")
        await callback_query.message.edit_text("🏠 Menu utama. Ketik /dashboard")

    @app.on_callback_query(filters.regex(r"^batal_cari$"), group=4)
    async def cancel_search(client: Client, callback_query: CallbackQuery):
        log.info(f"[CB] batal_cari oleh user_id={callback_query.from_user.id}")
        await callback_query.answer("❌ Pencarian dibatalkan.")
        await callback_query.message.edit_text("Ketik /cari untuk mulai ulang.")
