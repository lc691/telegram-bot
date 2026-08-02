# dcst_mbot/usecases/repost/title_parser.py

import re
from html import unescape
from pyrogram.types import Message


def extract_title_from_message(message: Message) -> tuple[str, str]:
    """
    Return:
    - title_db      : judul ASLI
    - title_display : judul bersih untuk UI/log
    """

    caption = message.caption or ""
    lines = [line.strip() for line in caption.splitlines()]

    title = ""

    for line in lines:

        # Cari line title
        if not line.startswith("🎬"):
            continue

        # Hapus HTML tag
        clean = re.sub(r"<.*?>", "", line)

        # Decode HTML entity
        clean = unescape(clean)

        # Hapus emoji title
        clean = clean.replace("🎬", "").strip()

        title = clean
        break

    if not title:
        return "", ""

    # Versi display/log
    title_display = re.sub(r"[^\w\s]", "", title).strip()

    return title, title_display