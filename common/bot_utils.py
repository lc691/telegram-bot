# common/bot_utils.py

from typing import Optional

from pyrogram import Client

from bots.bots_registry import get_bot

# Mapping nama bot ke nama tabel database
BOT_TABLE_MAP = {
    "drac1n": "users",
    "glow": "users",
}


def get_clean_bot_key(bot_key: str) -> str:
    """
    Menghapus suffix "_bot" dari bot_key, jika ada.
    """
    return bot_key[:-4] if bot_key.endswith("_bot") else bot_key


def resolve_bot(source_bot: str, fallback: Optional[Client] = None) -> Client:
    clean_key = get_clean_bot_key(source_bot)
    bot = get_bot(clean_key) or fallback

    if not bot:
        raise RuntimeError(f"Bot instance not found for source_bot={source_bot}")

    return bot


def get_table_name(source_bot: str) -> Optional[str]:
    """
    Mengembalikan nama tabel database untuk bot tertentu.
    Jika bot tidak dikenal, hasilnya None.
    """
    clean_bot = get_clean_bot_key(source_bot)
    return BOT_TABLE_MAP.get(clean_bot)
