import asyncio
from configs.logging_setup import log
from .constants import CHECK_INTERVAL_SECONDS
from .queries import run_retention
from .conversion import check_conversions
from .adaptive import update_failures
from .alert import retention_summary, check_low_conversion_alert


async def heavy_retention_loop(app, pool, stop_event):
    while not stop_event.is_set():
        try:
            await run_retention(app, pool)
            await check_conversions(pool)
            await update_failures(pool)
            await retention_summary(pool)
            await check_low_conversion_alert(app, pool)
        except Exception:
            log.exception("Retention loop error")

        try:
            await asyncio.wait_for(
                stop_event.wait(),
                timeout=CHECK_INTERVAL_SECONDS,
            )
        except asyncio.TimeoutError:
            continue
