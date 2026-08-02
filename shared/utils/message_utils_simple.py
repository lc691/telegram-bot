import asyncio
from pyrogram.enums import ParseMode
from pyrogram.errors import FloodWait
from pyrogram.types import Message

from configs.logging_setup import log


async def send_user_message(
    message: Message,
    text: str,
    parse_mode=ParseMode.HTML,
    retry=1,
    **kwargs,
):
    """
    UTIL PESAN NON-MENU:
    - error
    - notifikasi
    - info sementara
    """

    try:
        await message.reply_text(
            text,
            parse_mode=parse_mode,
            **kwargs,
        )
        return "sent"

    except FloodWait as e:
        if retry > 0:
            await asyncio.sleep(e.value)
            return await send_user_message(
                message,
                text,
                parse_mode=parse_mode,
                retry=retry - 1,
                **kwargs,
            )

        log.error("[send_user_message] FloodWait retry habis")
        return "failed"

    except Exception as e:
        log.error("[send_user_message] Gagal kirim pesan: %s", e)
        return "failed"
