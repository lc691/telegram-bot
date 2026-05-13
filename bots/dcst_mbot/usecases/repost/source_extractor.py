import re
from html import unescape
from pyrogram.types import Message


def extract_source_label(message: Message) -> str:
    """
    Extract source label dari caption (support format baru).

    Handle:
    - 🍿 ReelShort
    - 🍿 ReelShort | 📚 LIST DRAMA
    - HTML <a> tag
    """

    caption = message.caption or ""
    lines = [line.strip() for line in caption.splitlines()]

    for i, line in enumerate(lines):
        if line.startswith("💵"):
            for next_line in lines[i + 1:]:
                if not next_line:
                    continue

                # 1. Hilangkan HTML tag (kalau ada)
                clean = re.sub(r"<.*?>", "", next_line)

                # 2. Decode HTML entities
                clean = unescape(clean)

                # 3. Ambil sebelum "|"
                clean = clean.split("|")[0]

                # 4. Hapus emoji depan
                clean = re.sub(r"^[^\w]+", "", clean)

                return clean.strip()

            break

    return ""