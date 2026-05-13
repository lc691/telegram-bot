from typing import List, Union

from pyrogram import Client, filters
from pyrogram.types import Message

from configs.logging_setup import log
from config import POSTING_CHANNEL
from ....usecases.repost.repost_flow import run_repost_flow


# ==========================================================
# BACKUP CHANNEL CONFIGURATION
# ==========================================================
# Dapat berupa:
# - String tunggal: "@DramaMint"
# - String dipisahkan koma: "@DramaMint, @dramaglow"
# - List: ["@DramaMint", "@dramaglow"]
BACKUP_CHANNEL: Union[str, List[str]] = [
    "@DramaMint",
    "@dramaglow",
]


def _normalize_channels(channels: Union[str, List[str], None]) -> List[Union[str, int]]:
    """
    Normalisasi channel menjadi list yang valid untuk Pyrogram.

    Args:
        channels: String atau list channel.

    Returns:
        List channel yang sudah dibersihkan.
    """
    if not channels:
        return []

    # Jika berupa string, ubah menjadi list
    if isinstance(channels, str):
        channels = channels.split(",")

    normalized = []
    for ch in channels:
        ch = str(ch).strip()
        if not ch:
            continue

        # Konversi ke integer jika berupa chat ID
        if ch.lstrip("-").isdigit():
            normalized.append(int(ch))
        else:
            normalized.append(ch)

    return normalized


def register_repost_handler(app: Client) -> None:
    """
    Mendaftarkan handler untuk repost otomatis dari channel utama
    ke backup channel.
    """
    try:
        posting_channel = (
            int(POSTING_CHANNEL)
            if str(POSTING_CHANNEL).lstrip("-").isdigit()
            else POSTING_CHANNEL
        )
    except Exception:
        log.error("[REPOST] POSTING_CHANNEL tidak valid.")
        return

    backup_channels = _normalize_channels(BACKUP_CHANNEL)

    log.info(f"[REPOST] Handler registered for: {posting_channel}")
    log.info(f"[REPOST] Backup channels: {backup_channels}")

    @app.on_message(filters.chat(posting_channel))
    async def repost_handler(client: Client, message: Message):
        """
        Handler untuk memproses repost setelah pesan dikirim
        ke channel utama.
        """
        try:
            log.info(
                "[REPOST] Triggered | chat_id=%s | message_id=%s",
                message.chat.id,
                message.id,
            )

            await run_repost_flow(
                client=client,
                message=message,
                posting_channel=posting_channel,
                backup_channel=backup_channels,
            )

        except Exception as e:
            log.exception(f"[REPOST] Fatal error: {e}")
