import asyncio
import time
from typing import Set

import psutil
from pyrogram import Client
from pyrogram.enums import ParseMode

from shared.task_monitor import TaskMonitor
from configs.logging_setup import log


DEFAULT_CHECK_INTERVAL = 300
DEFAULT_WARN_COOLDOWN = 1800


async def monitor_memory(
    *,
    app: Client,
    admin_ids: Set[int],
    task_monitor: TaskMonitor,
    stop_event: asyncio.Event,
    threshold_mb: int,
    check_interval: int = DEFAULT_CHECK_INTERVAL,
    warn_cooldown: int = DEFAULT_WARN_COOLDOWN,
):
    """
    Lightweight memory watchdog.
    Non-critical monitor.
    """

    process = psutil.Process()

    last_warn_at: float | None = None

    log.info(
        "[MEMORY] monitor started threshold=%sMB",
        threshold_mb,
    )

    try:

        while not stop_event.is_set():

            memory_mb = (
                process.memory_info().rss
                / 1024
                / 1024
            )

            now = time.time()

            task_monitor.beat(
                "memory_monitor"
            )

            # =========================================
            # HIGH MEMORY
            # =========================================

            if memory_mb >= threshold_mb:

                should_warn = (
                    not last_warn_at
                    or now - last_warn_at >= warn_cooldown
                )

                if should_warn:

                    last_warn_at = now

                    log.warning(
                        "[MEMORY] high usage %.1fMB limit=%sMB",
                        memory_mb,
                        threshold_mb,
                    )

                    if admin_ids:

                        text = (
                            "⚠️ <b>MEMORI TINGGI</b>\n\n"
                            f"Penggunaan: <b>{memory_mb:.1f} MB</b>\n"
                            f"Batas: <b>{threshold_mb} MB</b>\n\n"
                            "Sistem tetap berjalan."
                        )

                        await asyncio.gather(
                            *(
                                app.send_message(
                                    admin_id,
                                    text,
                                    parse_mode=ParseMode.HTML,
                                )
                                for admin_id in admin_ids
                            ),
                            return_exceptions=True,
                        )

            # =========================================
            # BACK TO NORMAL
            # =========================================

            elif last_warn_at:

                log.info(
                    "[MEMORY] usage normal %.1fMB",
                    memory_mb,
                )

                last_warn_at = None

            # =========================================
            # SLEEP
            # =========================================

            try:

                await asyncio.wait_for(
                    stop_event.wait(),
                    timeout=check_interval,
                )

            except asyncio.TimeoutError:
                pass

    except asyncio.CancelledError:

        log.info(
            "[MEMORY] monitor stopped"
        )

    except Exception:

        log.exception(
            "[MEMORY] monitor failed"
        )

        raise
