from pyrogram import Client, filters
from pyrogram.types import Message

from apps.drac1n_bot.usecases.admin.voucher.create_voucher_flow import handle_voucher_command
from apps.drac1n_bot.decorators.admin_only import admin_only

VOUCHER_GROUP = 1


def register_voucher_command_handler(app: Client):
    @app.on_message(
        filters.command("voucher") & filters.private,
        group=VOUCHER_GROUP,
    )
    @admin_only()
    async def voucher_handler(client: Client, message: Message):
        await handle_voucher_command(client, message)
