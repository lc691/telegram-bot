from pyrogram import Client, filters
from pyrogram.enums import ParseMode
from pyrogram.types import Message

from ..usecases.resolve_info_target import resolve_info_target
from ..usecases.get_user_info import get_user_info
from ..presenters.info_formatter import format_info_text


def register_info_cmd_handler(app: Client):
    @app.on_message(filters.command("info"))
    async def info_handler(client: Client, message: Message):
        target_user = await resolve_info_target(client, message)

        user_id = target_user.id
        username = (
            f"@{target_user.username}"
            if target_user.username
            else "— Tidak ada —"
        )

        info = get_user_info(user_id)

        text = format_info_text(
            user_id=user_id,
            username=username,
            is_vip=info["is_vip"],
            vip_start=info["vip_start"],
            vip_expired=info["vip_expired"],
            is_private=message.chat.type == "private",
        )

        await message.reply_text(
            text,
            parse_mode=ParseMode.HTML,
            quote=True,
        )
