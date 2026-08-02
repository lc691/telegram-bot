from typing import Literal

from pyrogram import Client
from pyrogram.enums import ParseMode

from infrastructure.telegram.bots_registry import get_main_bot
from configs.logging_setup import log
from database.repositories.admin.admin_query import get_all_admins

LogLevel = Literal["info", "warning", "error"]


async def send_admin_log(
    client: Client,
    message: str,
    level: LogLevel = "warning",
):
    """
    Core async admin logger.
    Dipakai BOT (async).
    """

    # 🔒 hanya bot utama
    if client != get_main_bot():
        log.debug("[SEND_ADMIN_LOG] Skip: bukan bot utama")
        return

    # 📝 local log
    match level:
        case "info":
            log.info(message)
        case "error":
            log.error(message)
        case _:
            log.warning(message)

    try:
        admins = get_all_admins()
    except Exception:
        log.exception("[SEND_ADMIN_LOG] Gagal ambil admin")
        return

    if not admins:
        log.warning("[SEND_ADMIN_LOG] Admin kosong")
        return

    for admin in admins:
        try:
            await client.send_message(
                chat_id=admin["user_id"],
                text=f"⚠️ <b>Admin Log:</b>\n{message}",
                parse_mode=ParseMode.HTML,
                disable_notification=(level != "error"),
            )
        except Exception:
            log.exception(
                "[SEND_ADMIN_LOG] Gagal kirim ke admin %s",
                admin["user_id"],
            )
