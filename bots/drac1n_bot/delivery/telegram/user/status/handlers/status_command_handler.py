from typing import Union

from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, Message
from ..usecases.show_status_menu import show_status_menu
GROUP_STATUS = 1
GROUP_VIP_STATUS = 11


def register_status_cmd_handler(app, admin_cache):

    @app.on_message(filters.command("status"), group=GROUP_STATUS)
    async def status_cmd(_, message: Message):
        if message.chat.type in ("group", "supergroup"):
            await message.reply_text(
                "⚠️ Untuk melihat status lengkap, silakan chat langsung dengan saya di PM.\n\n"
                "👉 [Klik di sini](t.me/drac1n_bot?start=status)",
                disable_web_page_preview=True,
            )
            return

        await show_status_menu(
            event=message,
            admin_cache=admin_cache,
        )

    @app.on_callback_query(filters.regex("^vip_status$"), group=GROUP_VIP_STATUS)
    async def status_callback(_, cq: CallbackQuery):
        await cq.answer()

        await show_status_menu(
            event=cq,
            admin_cache=admin_cache,
        )
