import asyncio

from typing import Literal

from pyrogram import Client
from pyrogram.enums import ParseMode

from bots.bots_registry import get_main_bot
from configs.logging_setup import log
from db.admin.admin_query import get_all_admins

LogLevel = Literal["info", "warning", "error"]


def _format_message(message: str, level: LogLevel) -> str:
    icon = {
        "info": "ℹ️",
        "warning": "⚠️",
        "error": "❌",
    }.get(level, "⚠️")

    # Hindari crash Markdown
    safe_message = message.replace("```", "`\u200b``")

    return f"{icon} <b>Pemberitahuan Admin</b>\n\n{safe_message}"


async def log_to_admin(
    client: Client,
    message: str,
    level: LogLevel = "warning",
):
    """
    Kirim notifikasi ke semua admin Telegram.
    Hanya aktif jika dipanggil oleh bot utama.
    """

    # 🔒 Batasi hanya bot utama
    main_bot = get_main_bot()
    if client != main_bot:
        log.debug("[NOTIFY_ADMIN] Dilewati, bukan bot utama.")
        return

    log_msg = f"[NOTIFY_ADMIN] level={level} | {message}"

    match level:
        case "info":
            log.info(log_msg)
        case "error":
            log.error(log_msg)
        case _:
            log.warning(log_msg)

    try:
        admins = get_all_admins()
    except Exception:
        log.exception("[NOTIFY_ADMIN] Gagal load daftar admin")
        return

    if not admins:
        log.warning("[NOTIFY_ADMIN] Tidak ada admin ditemukan.")
        return

    text = _format_message(message, level)

    async def _send(admin_id: int):
        try:
            await client.send_message(
                chat_id=admin_id,
                text=text,
                parse_mode=ParseMode.HTML,
                disable_notification=(level != "error"),
            )
        except Exception:
            log.exception(
                "[NOTIFY_ADMIN] Gagal kirim ke admin %s",
                admin_id,
            )

    # 🚀 Kirim paralel (lebih cepat, tetap aman)
    await asyncio.gather(
        *(_send(admin["user_id"]) for admin in admins),
        return_exceptions=True,
    )
