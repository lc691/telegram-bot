from pyrogram import Client, filters
from pyrogram.enums import ChatType, ParseMode
from pyrogram.types import Message

from ..usecases.resolve_info_target import resolve_info_target
from ..usecases.get_user_info import get_user_info
from ..presenters.info_formatter import format_info_text


def register_info_cmd_handler(app: Client):

    @app.on_message(filters.command("info"))
    async def info_handler(client: Client, message: Message):

        try:
            target_user = await resolve_info_target(client, message)

            if not target_user:
                return await message.reply_text(
                    "❌ User tidak ditemukan.",
                    quote=True,
                )

            info = get_user_info(target_user.id)

            username = (
                f"@{target_user.username}"
                if target_user.username
                else None
            )

            first_name = target_user.first_name

            is_private = message.chat.type == ChatType.PRIVATE

            text = format_info_text(
                user_id=target_user.id,
                username=username,
                first_name=first_name,
                is_vip=info.get("is_vip", False),
                vip_start=info.get("vip_start"),
                vip_expired=info.get("vip_expired"),
                is_private=is_private,
            )

            await message.reply_text(
                text,
                parse_mode=ParseMode.HTML,
                quote=True,
            )

        except Exception as e:
            await message.reply_text(
                f"❌ Terjadi kesalahan:\n<code>{e}</code>",
                parse_mode=ParseMode.HTML,
                quote=True,
            )