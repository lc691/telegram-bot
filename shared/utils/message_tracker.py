from pyrogram import Client
from pyrogram.enums import ParseMode
from pyrogram.types import InlineKeyboardMarkup

from .message_cache import clear_last_message, get_last_message, set_last_message


async def try_edit_last_message(
    client: Client,
    user_id: int,
    text: str,
    markup: InlineKeyboardMarkup = None,
    parse_mode: str = ParseMode.MARKDOWN,
) -> str:
    """
    Mencoba mengedit pesan terakhir yang disimpan. Kembalikan:
    - 'edited' jika berhasil
    - 'not_found' jika tidak ada pesan sebelumnya
    - 'failed' jika gagal mengedit
    """
    prev = get_last_message(user_id)
    if not prev:
        return "not_found"

    chat_id, msg_id = prev
    try:
        await client.edit_message_text(
            chat_id=chat_id,
            message_id=msg_id,
            text=text,
            parse_mode=parse_mode,
            reply_markup=markup,
            disable_web_page_preview=True,
        )
        return "edited"
    except Exception:
        return "failed"


def save_last_sent_message(user_id: int, message) -> None:
    """
    Menyimpan pesan terakhir yang baru dikirim.
    """
    set_last_message(user_id, message.chat.id, message.id)


def forget_last_message(user_id: int) -> None:
    """
    Menghapus pesan terakhir dari cache.
    """
    clear_last_message(user_id)
