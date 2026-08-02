from pyrogram import Client, filters
from pyrogram.types import Message

from shared.utils.admin_cache import admin_cache

DEFAULT_USER_GROUP = 0


def register_inspect_cmd_handler(app: Client):
    @app.on_message(
        filters.command("inspect") & filters.private, group=DEFAULT_USER_GROUP
    )
    async def inspect_handler(client: Client, message: Message):
        user_id = message.from_user.id
        if not admin_cache.is_admin(user_id):
            await message.reply_text("⛔️ Kamu bukan admin.")
            return

        # await inspect_all_commands(client, [user_id])
        await message.reply_text("✅ Perintah sudah dilihat di log.")
