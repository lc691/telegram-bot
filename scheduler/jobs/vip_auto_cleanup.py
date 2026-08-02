import asyncio

from typing import Optional
from zoneinfo import ZoneInfo

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pyrogram import Client

from shared.utils.admin_notifier import (
    notify_admin_error,
    notify_admin_info,
)
from configs.logging_setup import log
from database.vip_users.vip_utils import (
    deactivate_expired_vips,
    sync_vip_status,
)

# =========================
# Scheduler State
# =========================
_scheduler: Optional[AsyncIOScheduler] = None
TIMEZONE = ZoneInfo("Asia/Jakarta")
JOB_ID = "vip_auto_cleanup"


# =========================
# Public API
# =========================
def start_vip_auto_cleanup(client: Client, interval_hours: int = 6) -> None:
    """
    Start VIP auto cleanup scheduler (idempotent).
    """
    global _scheduler

    if _scheduler and _scheduler.running:
        log.warning("[AUTO VIP] Scheduler sudah berjalan, dilewati.")
        return

    _scheduler = AsyncIOScheduler(timezone=TIMEZONE)

    _scheduler.add_job(
        vip_cleanup_task,
        trigger="interval",
        hours=interval_hours,
        args=[client],
        id=JOB_ID,
        replace_existing=True,
        max_instances=1,
        coalesce=True,
        misfire_grace_time=300,
    )

    _scheduler.start()
    log.info(
        "[AUTO VIP] ⏰ Scheduler aktif (WIB, tiap %s jam).",
        interval_hours,
    )


def stop_vip_auto_cleanup() -> None:
    """
    Gracefully stop scheduler (for shutdown / reload).
    """
    global _scheduler

    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        log.info("[AUTO VIP] Scheduler dihentikan.")

    _scheduler = None


async def run_vip_cleanup_once(client: Client) -> None:
    """
    Manual / cron execution.
    """
    await vip_cleanup_task(client)


# =========================
# Core Task
# =========================
async def vip_cleanup_task(client: Client) -> None:
    """
    Core VIP cleanup task.
    Safe for scheduler & manual execution.
    """
    if not client.is_connected:
        log.warning("[AUTO VIP] Client belum terkoneksi, task dilewati.")
        return

    try:
        affected, synced = await _run_cleanup_in_thread()

        message = (
            f"[AUTO VIP] ✅ {affected} VIP expired dinonaktifkan.\n"
            f"[AUTO VIP] 🔄 {synced} status VIP disinkronkan."
        )

        log.info(message)
        await _safe_notify_info(client, message)

    except Exception as exc:
        await _handle_cleanup_error(client, exc)


# =========================
# Internal Helpers
# =========================
async def _run_cleanup_in_thread() -> tuple[int, int]:
    """
    Run blocking DB operations in thread pool.
    """
    affected = await asyncio.to_thread(deactivate_expired_vips)
    synced = await asyncio.to_thread(sync_vip_status)
    return affected, synced


async def _handle_cleanup_error(client: Client, exc: Exception) -> None:
    msg = (
        f"[AUTO VIP] ❌ Auto-cleanup gagal "
        f"({type(exc).__name__}): {exc}"
    )

    log.error(msg, exc_info=True)

    await _safe_notify_error(client, msg)


async def _safe_notify_info(client: Client, message: str) -> None:
    try:
        await notify_admin_info(client, message)
    except Exception as notif_err:
        log.warning(
            "[AUTO VIP] ⚠️ Gagal kirim notifikasi info: %s",
            notif_err,
        )


async def _safe_notify_error(client: Client, message: str) -> None:
    try:
        await notify_admin_error(client, message)
    except Exception as notif_err:
        log.warning(
            "[AUTO VIP] ⚠️ Gagal kirim notifikasi error: %s",
            notif_err,
        )
