from pyrogram import Client

from config import REQUIRED_CHANNELS
from configs.logging_setup import log


async def validate_required_channels(app: Client):
    # log.info("🔎 Memeriksa keanggotaan bot di channel yang diwajibkan...")
    for username, _ in REQUIRED_CHANNELS:
        try:
            chat = await app.get_chat(username)
            # log.info(f"✅ Bot sudah join ke: {chat.title} ({username})")
        except Exception as e:
            log.error(f"❌ Bot belum join atau tidak bisa akses: {username} — {e}")
