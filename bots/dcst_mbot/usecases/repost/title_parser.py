# dcst_mbot/usecases/repost/title_parser.py
import re
from pyrogram.types import Message


def extract_title_from_message(message: Message) -> tuple[str, str]:
    """
    Return:
    - title_db      : judul ASLI (disimpan ke DB)
    - title_display : judul bersih (untuk UI/log)
    """
    caption = message.caption or ""
    title = caption.split("\n")[0].strip()

    if not title:
        return "", ""

    title_display = re.sub(r"[^\w\s]", "", title).strip()
    return title, title_display
