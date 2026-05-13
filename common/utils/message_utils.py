from pyrogram import Client
from pyrogram.enums import ParseMode
from pyrogram.errors import MessageNotModified
from pyrogram.types import CallbackQuery, InlineKeyboardMarkup, Message
from pyrogram.types import InputMediaDocument, InputMediaPhoto, InputMediaVideo
from common.utils.message_cache import (
    clear_last_message,
    get_last_message,
    set_last_message,
)
from configs.logging_setup import log


async def safe_send_or_edit(
    client: Client,
    user_id: int,
    text: str,
    markup: InlineKeyboardMarkup = None,
    parse_mode: ParseMode = ParseMode.HTML,
    disable_web_page_preview: bool = True,
    event: Message | CallbackQuery | None = None,
) -> str:
    try:
        prev = get_last_message(user_id)
        if prev:
            chat_id, msg_id = prev

            if chat_id != user_id:
                clear_last_message(user_id)
            else:
                try:
                    await client.edit_message_text(
                        chat_id=chat_id,
                        message_id=msg_id,
                        text=text,
                        parse_mode=parse_mode,
                        disable_web_page_preview=disable_web_page_preview,
                        reply_markup=markup,
                    )
                    set_last_message(user_id, chat_id, msg_id)
                    log.info("[safe_send_or_edit] ✅ Edit sukses user_id=%s", user_id)
                    return "modified"

                except MessageNotModified:
                    return "skipped"

                except Exception as e:
                    log.warning(
                        "[safe_send_or_edit] ⚠️ Edit gagal msg_id=%s err=%s",
                        msg_id,
                        e,
                    )
                    clear_last_message(user_id)

        # SEND NEW
        if isinstance(event, CallbackQuery) and event.message:
            msg = await event.message.reply_text(
                text,
                parse_mode=parse_mode,
                disable_web_page_preview=disable_web_page_preview,
                reply_markup=markup,
            )
        elif isinstance(event, Message):
            msg = await event.reply_text(
                text,
                parse_mode=parse_mode,
                disable_web_page_preview=disable_web_page_preview,
                reply_markup=markup,
            )
        else:
            msg = await client.send_message(
                chat_id=user_id,
                text=text,
                parse_mode=parse_mode,
                disable_web_page_preview=disable_web_page_preview,
                reply_markup=markup,
            )

        set_last_message(user_id, msg.chat.id, msg.id)
        log.info("[safe_send_or_edit] 📨 Pesan baru dikirim user_id=%s", user_id)
        return "sent"

    except Exception as e:
        log.error(
            "[safe_send_or_edit] ❌ Fatal user_id=%s err=%s",
            user_id,
            e,
            exc_info=True,
        )
        return "failed"


async def safe_edit_message(message, target_row, caption, keyboard):
    """
    Edit pesan hanya jika ada perubahan media / caption / keyboard.
    """

    # --- Ambil media lama ---
    old_caption = message.caption or ""
    old_keyboard = message.reply_markup
    old_media_id = None

    if message.video:
        old_media_id = message.video.file_id
    elif message.document:
        old_media_id = message.document.file_id
    elif message.photo:
        old_media_id = message.photo[-1].file_id  # FIX

    # --- Tentukan media baru ---
    file_id = target_row["file_id"]
    file_type = target_row["file_type"]

    if file_type == "video":
        new_media = InputMediaVideo(
            media=file_id,
            caption=caption,
            parse_mode=ParseMode.HTML,
        )
    elif file_type == "document":
        new_media = InputMediaDocument(
            media=file_id,
            caption=caption,
            parse_mode=ParseMode.HTML,
        )
    else:
        new_media = InputMediaPhoto(
            media=file_id,
            caption=caption,
            parse_mode=ParseMode.HTML,
        )

    # --- Bandingkan perubahan ---
    same_media = file_id == old_media_id
    same_caption = caption == old_caption
    same_keyboard = (
        (old_keyboard.inline_keyboard if old_keyboard else None)
        == (keyboard.inline_keyboard if keyboard else None)
    )

    if same_media and same_caption and same_keyboard:
        return "skipped"

    # --- Lakukan edit ---
    try:
        if not same_media:
            await message.edit_media(
                media=new_media,
                reply_markup=keyboard,
            )
            return "media_edited"

        await message.edit_caption(
            caption=caption,
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard,
        )
        return "caption_edited"

    except MessageNotModified:
        return "not_modified"

    except Exception as e:
        # penting untuk tracing silent-fail
        print(f"[safe_edit_message] edit failed: {e}")
        return "failed"