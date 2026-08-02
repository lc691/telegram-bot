import re
from html import unescape
from pyrogram.types import Message


def extract_source_label(message: Message) -> str:
    """
    Extract source label dari caption Telegram.

    Support:
    - 🌐 NetShort | 📚 LIST DRAMA
    - 🍿 ReelShort | 📚 LIST DRAMA
    - HTML / plain text
    """

    caption = message.caption or ""
    lines = [line.strip() for line in caption.splitlines()]

    for line in lines:

        # Cari line source
        if "LIST DRAMA" not in line.upper():
            continue

        # Hapus HTML
        clean = re.sub(r"<.*?>", "", line)

        # Decode HTML entity
        clean = unescape(clean)

        # Ambil sebelum "|"
        clean = clean.split("|")[0].strip()

        # Hapus emoji depan
        clean = re.sub(r"^[^\w]+", "", clean)

        return clean.strip()

    return ""