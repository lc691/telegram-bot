from pyrogram import Client, filters
from pyrogram.types import Message

from ..usecases.start_core import handle_start_command

DEFAULT_USER_GROUP = 1


def register_start_cmd_handler(app: Client, admin_cache):
    @app.on_message(
        filters.command("start") & filters.private,
        group=DEFAULT_USER_GROUP,
    )
    async def start_handler(client: Client, message: Message):
        """
        /start = ENTRY MENU
        WAJIB single-message UI (edit, bukan reply)
        """
        if not message.from_user:
            return

        await handle_start_command(client, message, admin_cache)
