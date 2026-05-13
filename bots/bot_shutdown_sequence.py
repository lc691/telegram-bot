# common/system/shutdown_sequence.py

import asyncio
from contextlib import suppress
from typing import Iterable

from pyrogram import Client

from common.task.vip_auto_cleanup import stop_vip_auto_cleanup
from common.task_monitor import TaskMonitor
from configs.logging_setup import log

_shutdown_lock = asyncio.Lock()
_shutdown_called = False


async def shutdown_sequence(
    *,
    bots: Iterable[Client],
    task_monitor: TaskMonitor,
    stop_events: Iterable[asyncio.Event] = (),
    pool=None,
    restart_event: asyncio.Event | None = None,
):
    """
    Graceful & idempotent shutdown.
    Urutan FIX – jangan diubah.
    """

    global _shutdown_called

    async with _shutdown_lock:
        if _shutdown_called:
            return
        _shutdown_called = True

    log.warning("🛑 SHUTDOWN SEQUENCE DIMULAI")

    # ==================================================
    # 0. STOP GLOBAL SCHEDULER
    # ==================================================
    stop_vip_auto_cleanup()

    # ==================================================
    # 1. SIGNAL ALL STOP EVENTS
    # ==================================================
    for ev in stop_events:
        ev.set()

    await asyncio.sleep(0)  # yield

    # ==================================================
    # 2. STOP TASK MONITOR (NO MORE RESTART)
    # ==================================================
    with suppress(Exception):
        await task_monitor.stop()

    # ==================================================
    # 3. STOP ALL BOTS (RELEASE NETWORK FIRST)
    # ==================================================
    async def stop_bot(bot: Client):
        try:
            if bot.is_connected:
                await bot.stop()
                log.info("🤖 Bot stopped: %s", bot.name)
        except Exception:
            log.exception("❌ Gagal stop bot: %s", getattr(bot, "name", "?"))

    await asyncio.gather(
        *(stop_bot(bot) for bot in bots),
        return_exceptions=True,
    )

    # ==================================================
    # 4. CANCEL LEFTOVER TASKS (SAFE SCOPE)
    # ==================================================
    current = asyncio.current_task()

    pending = [
        t for t in asyncio.all_tasks()
        if t is not current
        and not t.done()
        and t.get_name() != "task-monitor-loop"
    ]

    if pending:
        log.info("🧹 Cancel %d leftover tasks", len(pending))

        for task in pending:
            task.cancel()

        with suppress(asyncio.CancelledError):
            await asyncio.gather(*pending, return_exceptions=True)

    # ==================================================
    # 5. CLOSE DB POOL (LAST RESOURCE)
    # ==================================================
    if pool:
        with suppress(Exception):
            await pool.close()
            log.info("🗄️ DB pool closed")

    # ==================================================
    # 6. TRIGGER RESTART (OPTIONAL, LAST STEP)
    # ==================================================
    if restart_event and not restart_event.is_set():
        restart_event.set()
        log.warning("🔁 Restart event triggered")

    log.warning("✅ SHUTDOWN SEQUENCE SELESAI (BERSIH)")
