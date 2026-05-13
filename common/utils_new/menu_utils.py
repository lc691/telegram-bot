from pyrogram.enums import ParseMode
from pyrogram.errors import MessageNotModified
from pyrogram.types import CallbackQuery, Message

from configs.logging_setup import log


async def edit_menu(
    event: Message | CallbackQuery,
    text: str,
    markup=None,
    parse_mode=ParseMode.HTML,
    disable_web_page_preview=True,
):
    """
    MENU RENDERER
    - EDIT jika memungkinkan
    - SEND HANYA untuk bootstrap pertama (pesan user)
    """

    if isinstance(event, CallbackQuery):
        message = event.message
        client = event._client
        chat_id = message.chat.id

        try:
            await message.edit_text(
                text=text,
                reply_markup=markup,
                parse_mode=parse_mode,
                disable_web_page_preview=disable_web_page_preview,
            )
            return "edited"

        except MessageNotModified:
            return "skipped"

        except Exception as e:
            log.error(
                "[edit_menu] callback edit failed msg_id=%s err=%s",
                message.id,
                e,
                exc_info=True,
            )
            return "failed"

    # ===============================
    # EVENT = MESSAGE (BOOTSTRAP)
    # ===============================
    if isinstance(event, Message):
        client = event._client
        chat_id = event.chat.id

        # Jika pesan dari USER → tidak bisa diedit
        if event.from_user and event.from_user.is_bot is False:
            await client.send_message(
                chat_id=chat_id,
                text=text,
                reply_markup=markup,
                parse_mode=parse_mode,
                disable_web_page_preview=disable_web_page_preview,
            )
            return "sent"

        # Jika pesan dari BOT → boleh diedit
        try:
            await event.edit_text(
                text=text,
                reply_markup=markup,
                parse_mode=parse_mode,
                disable_web_page_preview=disable_web_page_preview,
            )
            return "edited"

        except MessageNotModified:
            return "skipped"

        except Exception as e:
            log.error(
                "[edit_menu] message edit failed msg_id=%s err=%s",
                event.id,
                e,
                exc_info=True,
            )
            return "failed"
