import asyncio
import psutil

from configs.logging_setup import log


async def memory_metrics_logger(
    *,
    stop_event: asyncio.Event,
    interval_hours: int = 2,
):
    """
    Periodic RAM metrics logger.
    Log RSS memory tiap X jam.
    """
    process = psutil.Process()
    interval_sec = interval_hours * 3600

    log.info(
        "[MEMORY] Metrics logger started | interval=%dh",
        interval_hours,
    )

    while not stop_event.is_set():
        try:
            rss_mb = process.memory_info().rss / (1024 * 1024)
            log.info(
                "[MEMORY] Usage snapshot: %.1f MB",
                rss_mb,
            )

            await asyncio.wait_for(
                stop_event.wait(),
                timeout=interval_sec,
            )

        except asyncio.TimeoutError:
            continue
        except asyncio.CancelledError:
            break
        except Exception:
            log.exception("[MEMORY] Metrics logger error")
            await asyncio.sleep(60)

    log.info("[MEMORY] Metrics logger stopped")
