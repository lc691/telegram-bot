import asyncio

from configs.logging_setup import log
from refresh_trending import refresh_trending_cache


REFRESH_INTERVAL = 1800  # 30 menit


async def trending_refresh_loop(stop_event):

    while not stop_event.is_set():

        try:

            await asyncio.to_thread(
                refresh_trending_cache
            )

        except Exception:

            log.exception(
                "[TRENDING] refresh failed"
            )

        try:

            await asyncio.wait_for(
                stop_event.wait(),
                timeout=REFRESH_INTERVAL,
            )

        except asyncio.TimeoutError:
            pass


def start_trending_auto_refresh(task_monitor):

    stop_event = asyncio.Event()

    task = asyncio.create_task(
        trending_refresh_loop(stop_event),
        name="trending-refresh",
    )

    task_monitor.register(
        name="trending_refresh",
        task=task,
        critical=False,
    )

    log.info(
        "[STARTUP] trending refresh started"
    )

    return stop_event