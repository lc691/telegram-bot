import asyncio

import psutil

from configs.logging_setup import log


DEFAULT_INTERVAL_HOURS = 2


async def memory_metrics_logger(
    *,
    stop_event: asyncio.Event,
    interval_hours: int = DEFAULT_INTERVAL_HOURS,
):

    process = psutil.Process()

    interval_seconds = (
        interval_hours * 3600
    )

    try:

        while not stop_event.is_set():

            rss_mb = (
                process.memory_info().rss
                / 1024
                / 1024
            )

            log.info(
                "[MEMORY] usage %.1fMB",
                rss_mb,
            )

            try:

                await asyncio.wait_for(
                    stop_event.wait(),
                    timeout=interval_seconds,
                )

            except asyncio.TimeoutError:
                pass

    except asyncio.CancelledError:

        pass

    except Exception:

        log.exception(
            "[MEMORY] metrics logger failed"
        )