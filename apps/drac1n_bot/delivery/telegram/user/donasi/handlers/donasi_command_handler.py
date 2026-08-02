from pyrogram import Client, filters
from pyrogram.types import Message

from apps.drac1n_bot.delivery.telegram.user.donasi.usecases.show_donasi_menu import show_donasi_menu

DONASI_GROUP = 1


def register_donasi_cmd_handler(app: Client):
    @app.on_message(filters.command("donasi") & filters.private, group=DONASI_GROUP)
    async def donasi_command(client: Client, message: Message):
        await show_donasi_menu(client, message)
