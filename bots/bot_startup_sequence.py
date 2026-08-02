import asyncio
from pyrogram import Client

from common.bot_commands_scope import (
    apply_bot_commands,
    register_command_checker,
)
from common.messaging.notification_poller import run_notifier_loop
from common.utils.admin_cache import admin_cache
from common.webhook.reminder.reminder_loop import reminder_loop
from configs.logging_setup import log


# =====================================================
# === PUBLIC ENTRY (PER BOT, 1x) ======================
# =====================================================
async def startup_sequence(app: Client, bot_name: str) -> None:
    """
    Startup sequence khusus BOT.
    - Aman untuk polling
    - Tidak mengurus webhook
    - Idempotent
    """
    try:
        _setup_admin_commands(app)
        _start_bot_tasks(app, bot_name)

    except Exception:
        log.exception("Startup sequence failed: %s", bot_name)


# =====================================================
# === ADMIN COMMAND SETUP =============================
# =====================================================
def _setup_admin_commands(app: Client) -> None:
    """
    Setup command & admin checker (GLOBAL READ-ONLY).
    """
    async def _init():
        admin_ids = tuple(await admin_cache.get_admin_ids())

        admin_cache.register_callback(
            lambda ids: apply_bot_commands(app, ids)
        )

        await apply_bot_commands(app, admin_ids)
        register_command_checker(app, admin_ids)

    asyncio.create_task(_init(), name="admin-command-setup")


# =====================================================
# === BOT TASKS (PER BOT) =============================
# =====================================================
def _start_bot_tasks(app: Client, bot_name: str) -> None:
    """
    Start task yang memang milik BOT.
    """
    loop = asyncio.get_running_loop()
    existing = {t.get_name() for t in asyncio.all_tasks(loop)}

    bot_tasks = {
        f"{bot_name}-notifier": lambda: run_notifier_loop(app, bot_name),
    }

    for name, coro_factory in bot_tasks.items():
        if name in existing:
            continue

        asyncio.create_task(coro_factory(), name=name)
        log.debug("Bot task started: %s", name)


# =====================================================
# === GLOBAL TASKS (1x PER PROCESS) ===================
# =====================================================
def start_global_tasks_once(app: Client) -> None:
    """
    Task global yang hanya boleh jalan 1x per process.
    Dipanggil dari main.py.
    """
    loop = asyncio.get_running_loop()
    existing = {t.get_name() for t in asyncio.all_tasks(loop)}

    if "global-reminder" not in existing:
        asyncio.create_task(
            reminder_loop(app),
            name="global-reminder",
        )
        # log.info("Global reminder loop started")
