import asyncio

from pyrogram.enums import ParseMode
from pyrogram.errors import FloodWait, MessageNotModified, RPCError
from pyrogram.types import CallbackQuery, Message

from configs.logging_setup import log


async def safe_answer(
    callback_query: CallbackQuery, text=None, show_alert=False, cache_time=3
):
    try:
        await callback_query.answer(
            text=text,
            show_alert=show_alert,
            cache_time=cache_time,
        )
    except RPCError as e:
        log.warning(f"[safe_answer] Gagal menjawab callback: {e}")


async def safe_reply(
    message: Message, text: str, parse_mode=ParseMode.HTML, retry=1, **kwargs
):
    try:
        await message.reply_text(text, parse_mode=parse_mode, **kwargs)
    except FloodWait as e:
        if retry > 0:
            log.warning(f"[safe_reply] Flood wait {e.value} detik, retry...")
            await asyncio.sleep(e.value)
            await safe_reply(
                message, text, parse_mode=parse_mode, retry=retry - 1, **kwargs
            )
        else:
            log.error(f"[safe_reply] Retry habis, gagal reply ke user.")
    except Exception as e:
        log.warning(f"[safe_reply] Gagal kirim reply: {e}")


async def safe_edit_text(
    message: Message,
    new_text: str,
    reply_markup=None,
    parse_mode=ParseMode.HTML,
    disable_web_page_preview=True,
    **kwargs,
):
    try:
        current_text = (message.text or "").strip()
        if current_text.lower() == new_text.strip().lower():
            raise MessageNotModified()

        await message.edit_text(
            new_text,
            reply_markup=reply_markup,
            parse_mode=parse_mode,
            disable_web_page_preview=disable_web_page_preview,
            **kwargs,
        )
    except MessageNotModified:
        log.debug("[safe_edit_text] Tidak ada perubahan isi pesan.")
    except Exception as e:
        log.warning(f"[safe_edit_text] Gagal edit pesan (msg_id={message.id}): {e}")


async def safe_send_message(bot, chat_id, text, retry=1, **kwargs):
    try:
        await bot.send_message(chat_id, text, **kwargs)
    except FloodWait as e:
        if retry > 0:
            log.warning(f"[SAFE_SEND] Flood wait {e.value} detik, tunggu...")
            await asyncio.sleep(e.value)
            await safe_send_message(bot, chat_id, text, retry=retry - 1, **kwargs)
        else:
            log.error(f"[SAFE_SEND] Retry habis, gagal kirim pesan ke {chat_id}")
    except Exception as e:
        log.error(f"[SAFE_SEND] Gagal kirim pesan ke {chat_id}: {e}")


async def safe_delete_message(bot, chat_id: int, message_id: int, retry=1):
    try:
        await bot.delete_messages(chat_id, message_id)
    except FloodWait as e:
        if retry > 0:
            log.warning(f"[SAFE_DELETE] Flood wait {e.value} detik, retry...")
            await asyncio.sleep(e.value)
            await safe_delete_message(bot, chat_id, message_id, retry=retry - 1)
        else:
            log.error(f"[SAFE_DELETE] Retry habis, gagal hapus pesan.")
    except Exception as e:
        log.warning(f"[SAFE_DELETE] Gagal hapus pesan (msg_id={message_id}): {e}")
