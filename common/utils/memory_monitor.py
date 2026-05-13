import asyncio
import time
from contextlib import suppress
from typing import Set

import psutil
from pyrogram import Client
from pyrogram.enums import ParseMode

from common.task_monitor import TaskMonitor
from configs.logging_setup import log


async def monitor_memory(
    *,
    app: Client,
    admin_ids: Set[int],
    task_monitor: TaskMonitor,
    stop_event: asyncio.Event,
    threshold_mb: int,
    check_interval: int = 300,     # 5 menit cukup
    warn_cooldown: int = 1800,     # 30 menit (hemat spam & wakeup)
):
    """
    Lightweight memory watchdog.
    NON-CRITICAL, NON-RESTARTING.
    """

    process = psutil.Process()
    last_warn_at: float | None = None

    log.info(
        "[MEMORY] Monitor started | threshold=%s MB | interval=%ss",
        threshold_mb,
        check_interval,
    )

    try:
        while not stop_event.is_set():
            memory_mb = process.memory_info().rss / 1024 / 1024
            now = time.time()

            # heartbeat SANGAT JARANG (sekadar hidup)
            task_monitor.beat("memory_monitor")

            if memory_mb >= threshold_mb:
                if not last_warn_at or now - last_warn_at >= warn_cooldown:
                    last_warn_at = now

                    log.warning(
                        "[MEMORY] HIGH: %.2f MB (limit %s MB)",
                        memory_mb,
                        threshold_mb,
                    )

                    if admin_ids:
                        text = (
                            "⚠️ <b>MEMORI TINGGI</b>\n\n"
                            f"Penggunaan: <b>{memory_mb:.2f} MB</b>\n"
                            f"Batas: <b>{threshold_mb} MB</b>\n\n"
                            "Sistem tetap berjalan."
                        )

                        # kirim sekali per admin, tanpa loop agresif
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

            else:
                if last_warn_at:
                    log.info("[MEMORY] Normal kembali: %.2f MB", memory_mb)
                    last_warn_at = None

            # tidur panjang = hemat
            try:
                await asyncio.wait_for(stop_event.wait(), timeout=check_interval)
            except asyncio.TimeoutError:
                continue

    except asyncio.CancelledError:
        log.info("[MEMORY] Monitor dibatalkan")
    except Exception:
        log.exception("[MEMORY] Fatal error")
        raise
    finally:
        log.info("[MEMORY] Monitor stopped")
