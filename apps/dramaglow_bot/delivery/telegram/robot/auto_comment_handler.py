import asyncio
from pyrogram import Client, filters

from config import POSTING_CHANNEL, GROUP_DISKUSI
from configs.logging_setup import log

AUTO_COMMENT_TEXT = "https://t.me/c/3714147269/3"

# simple in-memory dedup (aman untuk satu instance)
_COMMENTED = set()


def register_auto_comment_handler(app: Client) -> None:
    @app.on_message(filters.group & (filters.text | filters.caption))
    async def _auto_comment_broadcast(client: Client, message):
        # =====================================================
        # 1. Pastikan ini hasil broadcast dari CHANNEL donasi
        # =====================================================
        fwd = message.forward_from_chat
        if not fwd:
            return

        if fwd.id != POSTING_CHANNEL:
            return

        # =====================================================
        # 2. Pastikan ini GROUP target
        # =====================================================
        if message.chat.id != GROUP_DISKUSI:
            return

        # =====================================================
        # 3. Anti double comment (WAJIB di production)
        # =====================================================
        if message.id in _COMMENTED:
            return
        _COMMENTED.add(message.id)

        # =====================================================
        # 4. Validasi konten (donasi)
        # =====================================================
        content = (message.text or message.caption or "").upper()
        if "DONASI" not in content:
            return

        log.info(
            "[DONATION][AUTO_COMMENT] broadcast detected "
            "channel_msg_id=%s group_msg_id=%s",
            message.forward_from_message_id,
            message.id,
        )

        # =====================================================
        # 5. AUTO COMMENT LANGSUNG DI POST BROADCAST
        # =====================================================
        await client.send_message(
            chat_id=message.chat.id,
            text=AUTO_COMMENT_TEXT,
            reply_to_message_id=message.id,  # 🔥 INTI SOLUSI
            disable_web_page_preview=True,  # opsional
        )
