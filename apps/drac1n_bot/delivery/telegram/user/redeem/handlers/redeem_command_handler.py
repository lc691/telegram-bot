from pyrogram import Client, filters
from pyrogram.types import Message

from ..usecases.redeem_flow import handle_redeem_command

REDEEM_GROUP = 40


def register_redeem_command_handler(app: Client):
    @app.on_message(
        filters.command("redeem") & filters.private,
        group=REDEEM_GROUP,
    )
    async def redeem_handler(client: Client, message: Message):
        await handle_redeem_command(client, message)
