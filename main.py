import os
import signal
import asyncio
import threading

import asyncpg
import uvicorn

from bots.bot_manager import BotManager
from bots.bot_shutdown_sequence import shutdown_sequence
from bots.bots_registry import register_bot

from configs.bots_config import BOT_CONFIG
from configs.logging_setup import setup_logger, log

from channel_validator import validate_required_channels
from common.task_monitor import TaskMonitor
from common.task.vip_auto_cleanup import start_vip_auto_cleanup
from common.utils.admin_cache import admin_cache
from common.utils.memory_monitor import monitor_memory
from common.utils.ui_session import start_ui_cleanup_loop
from bots.bot_startup_sequence import start_global_tasks_once
from common.task.heavy_retention import heavy_retention_loop

# 🔥 WEBHOOK KHUSUS PAYMENT / TRAKTEER
from common.webhook.trakteer_listener import app as webhook_app

from bots.caridrama_bot.infrastructure.memory.memory_metrics import (
    memory_metrics_logger,
)

from db.models import ensure_admins_table
from config import PGDATABASE, PGHOST, PGPASSWORD, PGPORT, PGUSER


# =====================================================
# GLOBAL CONTROL SIGNAL
# =====================================================
stop_event = asyncio.Event()
restart_event = asyncio.Event()
stop_event_thread = threading.Event()


# =====================================================
# DATABASE
# =====================================================
async def create_db_pool():
    try:
        return await asyncpg.create_pool(
            database=PGDATABASE,
            user=PGUSER,
            password=PGPASSWORD,
            host=PGHOST,
            port=PGPORT,
            min_size=1,
            max_size=2,  # hemat RAM VPS
        )
    except Exception as e:
        log.error("DB pool gagal: %s", e)
        return None


# =====================================================
# SIGNAL HANDLER (SYSTEMD / VPS SAFE)
# =====================================================
def setup_signals():
    def shutdown_signal():
        if not stop_event.is_set():
            stop_event.set()
            stop_event_thread.set()

    try:
        loop = asyncio.get_running_loop()
        loop.add_signal_handler(signal.SIGINT, shutdown_signal)
        loop.add_signal_handler(signal.SIGTERM, shutdown_signal)
    except (NotImplementedError, RuntimeError):
        threading.Thread(
            target=lambda: stop_event_thread.wait(),
            daemon=True,
        ).start()


# =====================================================
# GLOBAL STARTUP (RINGAN & WAJIB)
# =====================================================
async def startup_global_services():
    """
    Service global yang:
    - wajib
    - ringan
    - tidak tergantung bot
    """
    ensure_admins_table()

    await admin_cache.force_reload()
    log.warning("GLOBAL admin_cache id=%s", id(admin_cache))
    admin_cache.start_background_task()

    start_ui_cleanup_loop()


# =====================================================
# BOT STARTUP (TELEGRAM POLLING)
# =====================================================
async def start_bots(pool):
    """
    Start semua Telegram bot (POLLING MODE)
    """
    managers = [
        BotManager(
            name=name,
            factory=lambda cfg=cfg: cfg["factory"](pool),
            handler_register_func=cfg["register_handlers"],
            startup_func=cfg.get("startup"),
        )
        for name, cfg in BOT_CONFIG.items()
    ]

    active = []

    for manager in managers:
        if await manager.initialize():
            cfg = BOT_CONFIG.get(manager.name, {})
            bot_key = cfg.get("bot_key")
            if bot_key:
                register_bot(bot_key, manager.app)
            active.append(manager)

    if not active:
        raise RuntimeError("Tidak ada bot aktif")

    # validasi channel cukup sekali (pakai bot utama)
    await validate_required_channels(active[0].app)

    # VIP cleanup pakai bot utama
    start_vip_auto_cleanup(active[0].app)

    return active


# =====================================================
# OPTIONAL SERVICES (MONITORING + WEBHOOK PAYMENT)
# =====================================================
async def start_optional_services(admin_app, task_monitor):
    """
    Service tambahan:
    - monitoring
    - metrics
    - webhook payment (CRITICAL)
    """
    stop_events = []

    # ================= MEMORY MONITOR =================
    memory_stop = asyncio.Event()
    stop_events.append(memory_stop)

    memory_task = asyncio.create_task(
        monitor_memory(
            app=admin_app,
            admin_ids=set(await admin_cache.get_admin_ids()),
            task_monitor=task_monitor,
            stop_event=memory_stop,
            threshold_mb=600,
        ),
        name="memory-monitor",
    )

    task_monitor.register(
        name="memory_monitor",
        task=memory_task,
        critical=False,
    )

    # ================= MEMORY METRICS LOGGER =================
    metrics_stop = asyncio.Event()
    stop_events.append(metrics_stop)

    metrics_task = asyncio.create_task(
        memory_metrics_logger(
            stop_event=metrics_stop,
            interval_hours=2,
        ),
        name="memory-metrics",
    )

    task_monitor.register(
        name="memory_metrics",
        task=metrics_task,
        critical=False,
    )

    # ================= WEBHOOK PAYMENT (WAJIB) =================
    async def webhook_server():
        config = uvicorn.Config(
            webhook_app,
            host="0.0.0.0",
            port=int(os.getenv("PORT", 8080)),
            access_log=False,
            loop="asyncio",
            workers=1,  # ❗ JANGAN multi worker
        )
        server = uvicorn.Server(config)
        serve_task = asyncio.create_task(server.serve())

        await stop_event.wait()
        server.should_exit = True
        await serve_task

    webhook_task = asyncio.create_task(
        webhook_server(),
        name="webhook-payment",
    )

    task_monitor.register(
        name="webhook_payment",
        task=webhook_task,
        critical=True,
    )

    return stop_events


# =====================================================
# MAIN ASYNC APP
# =====================================================
async def run_app():
    setup_signals()

    pool = await create_db_pool()
    if not pool:
        log.warning("⚠️ Bot berjalan tanpa database")

    task_monitor = TaskMonitor()
    task_monitor.set_restart_event(restart_event)
    task_monitor.start(interval=60)

    await startup_global_services()

    bots = await start_bots(pool)
    admin_app = bots[0].app

    task_monitor.set_client(admin_app)

    stop_events = await start_optional_services(admin_app, task_monitor)

    # 🔥 START GLOBAL TASK (HANYA 1x)
    start_global_tasks_once(admin_app)

    # =====================================================
    # HEAVY RETENTION (SAFE VERSION)
    # =====================================================
    if pool:
        from common.task.heavy_retention import heavy_retention_loop

        retention_stop = asyncio.Event()

        retention_task = asyncio.create_task(
            heavy_retention_loop(
                app=admin_app,
                pool=pool,
                stop_event=retention_stop,
            ),
            name="heavy-retention",
        )

        task_monitor.register(
            name="heavy_retention",
            task=retention_task,
            critical=False,  # jangan bikin bot mati kalau error
        )

        stop_events.append(retention_stop)

    else:
        log.warning("Retention disabled (no database pool)")

    log.info("🤖 BOT READY | VPS MODE | Telegram=Polling | Webhook=Payment")

    await asyncio.wait(
        [
            asyncio.create_task(stop_event.wait()),
            asyncio.create_task(restart_event.wait()),
        ],
        return_when=asyncio.FIRST_COMPLETED,
    )

    await shutdown_sequence(
        bots=[b.app for b in bots],
        task_monitor=task_monitor,
        stop_events=[stop_event, *stop_events],
        pool=pool,
        restart_event=restart_event,
    )


# =====================================================
# ENTRY POINT
# =====================================================
def main():
    setup_logger()
    try:
        asyncio.run(run_app())
    except KeyboardInterrupt:
        log.warning("🛑 Dihentikan manual")
    except Exception:
        log.critical("💥 Fatal error", exc_info=True)


if __name__ == "__main__":
    main()
