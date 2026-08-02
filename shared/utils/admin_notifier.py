import asyncio

from pyrogram import Client

from infrastructure.telegram.bots_registry import get_main_bot

# ==================================================
# ASYNC API (UNTUK BOT / APSCHEDULER)
# ==================================================
from shared.utils.notify_admin_async import log_to_admin
from shared.utils.notify_admin_sync import send_admin_log
from configs.logging_setup import log


async def notify_admin_info(client: Client, message: str):
    await log_to_admin(client, message, level="info")


async def notify_admin_warning(client: Client, message: str):
    await log_to_admin(client, message, level="warning")


async def notify_admin_error(client: Client, message: str):
    await log_to_admin(client, message, level="error")


async def notify_admin(
    client: Client,
    message: str,
    level: str = "warning",
):
    await log_to_admin(client, message, level=level)


# ==================================================
# INTERNAL ASYNC RUNNER
# ==================================================
def _run_async(coro):
    try:
        asyncio.run(coro)
    except RuntimeError:
        loop = asyncio.get_event_loop()
        loop.create_task(coro)


# ==================================================
# SYNC API (CRON SAFE)
# ==================================================
def notify_admin_info_sync(message: str):
    _notify_admin_sync(message, level="info")


def notify_admin_warning_sync(message: str):
    _notify_admin_sync(message, level="warning")


def notify_admin_error_sync(message: str):
    _notify_admin_sync(message, level="error")


def _notify_admin_sync(message: str, level: str):
    """
    Aman untuk cron:
    - Bot belum start → SKIP telegram
    - Tidak pernah crash
    """
    try:
        bot = get_main_bot()

        if bot is None:
            log.warning(
                "[CRON][ADMIN_NOTIFY] Bot utama belum tersedia. "
                "Pesan tidak dikirim ke Telegram."
            )
            log.info("[CRON][ADMIN_NOTIFY] %s", message)
            return

        _run_async(send_admin_log(bot, message, level=level))

    except Exception:
        log.exception("[CRON] Gagal kirim notifikasi admin")
