import asyncio
import time

from contextlib import suppress
from typing import Callable, Dict, Optional

from pyrogram import Client

from common.utils.admin_notifier import notify_admin_error
from configs.logging_setup import log


class TaskMonitor:
    """
    GLOBAL task monitor (lightweight).
    - Monitor background task
    - Optional auto-restart (guarded)
    - Admin notify (throttled)
    """

    _instance: Optional["TaskMonitor"] = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, client: Optional[Client] = None):
        if getattr(self, "_initialized", False):
            return

        self.client = client

        self.tasks: Dict[str, asyncio.Task] = {}
        self.recovery_callbacks: Dict[str, Callable[[], asyncio.Task]] = {}
        self._critical_tasks: set[str] = set()

        self._heartbeats: Dict[str, float] = {}
        self._heartbeat_timeout: Dict[str, float] = {}

        self._last_restart: Dict[str, float] = {}
        self._restart_cooldown = 60  # ⬅️ anti restart storm

        self._last_notify: Dict[str, float] = {}
        self._notify_cooldown = 300

        self._stop_event = asyncio.Event()
        self._loop_task: Optional[asyncio.Task] = None
        self._restart_event: Optional[asyncio.Event] = None

        self._initialized = True

    # ==================================================
    # PUBLIC API
    # ==================================================
    def set_client(self, client: Client):
        self.client = client

    def set_restart_event(self, event: asyncio.Event):
        self._restart_event = event

    def start(self, interval: float = 60.0):  # ⬅️ lebih hemat
        if self._loop_task and not self._loop_task.done():
            return

        self._loop_task = asyncio.create_task(
            self._monitor_loop(interval),
            name="task-monitor-loop",
        )

    def register(
        self,
        name: str,
        task: asyncio.Task,
        on_fail_restart: Optional[Callable[[], asyncio.Future]] = None,
        critical: bool = False,
    ):
        self.tasks[name] = task

        if on_fail_restart:
            self.recovery_callbacks[name] = on_fail_restart

        if critical:
            self._critical_tasks.add(name)

    async def stop(self):
        self._stop_event.set()

        if self._loop_task:
            self._loop_task.cancel()
            with suppress(asyncio.CancelledError):
                await self._loop_task

        self._cleanup_all()
        log.info("🧹 TaskMonitor berhenti.")

    # ==================================================
    # INTERNAL LOOP
    # ==================================================
    async def _monitor_loop(self, interval: float):
        try:
            while not self._stop_event.is_set():
                await self._check_tasks()
                await asyncio.sleep(interval)
        except asyncio.CancelledError:
            pass

    async def _check_tasks(self):
        now = time.time()

        # --- heartbeat watchdog ---
        for name, last in list(self._heartbeats.items()):
            timeout = self._heartbeat_timeout.get(name)
            if timeout and now - last > timeout:
                msg = f"🧊 Task '{name}' freeze (>{timeout:.0f}s)"
                log.critical(msg)
                await self._notify_admin(name, msg)

                if name in self._critical_tasks and self._restart_event:
                    self._restart_event.set()
                self._cleanup_task(name)
                return

        # --- task lifecycle ---
        for name, task in list(self.tasks.items()):
            if not task.done():
                continue

            restart = False

            if task.cancelled():
                msg = f"⚠️ Task '{name}' dibatalkan."
            else:
                exc = task.exception()
                if exc:
                    msg = f"💥 Task '{name}' error:\n{exc}"
                    restart = True

                    if name in self._critical_tasks and self._restart_event:
                        log.critical("🚨 Critical task failed → restart process")
                        self._restart_event.set()
                        return
                else:
                    msg = f"ℹ️ Task '{name}' selesai."

            log.warning(msg)
            await self._notify_admin(name, msg)

            if restart:
                await self._restart_task(name)
            else:
                self._cleanup_task(name)

    async def _restart_task(self, name: str):
        now = time.time()
        last = self._last_restart.get(name, 0)

        if now - last < self._restart_cooldown:
            log.warning("⏳ Restart '%s' diblok (cooldown)", name)
            self._cleanup_task(name)
            return

        self._last_restart[name] = now
        restart_func = self.recovery_callbacks.get(name)

        if not restart_func:
            self._cleanup_task(name)
            return

        try:
            result = restart_func()
            task = result if isinstance(result, asyncio.Task) else asyncio.create_task(result)
            self.tasks[name] = task
            log.info("🔄 Task '%s' direstart.", name)
        except Exception:
            log.exception("❌ Gagal restart '%s'", name)
            self._cleanup_task(name)

    # ==================================================
    # CLEANUP
    # ==================================================
    def _cleanup_task(self, name: str):
        self.tasks.pop(name, None)
        self.recovery_callbacks.pop(name, None)
        self._critical_tasks.discard(name)
        self._heartbeats.pop(name, None)
        self._heartbeat_timeout.pop(name, None)
        self._last_restart.pop(name, None)

    def _cleanup_all(self):
        for name in list(self.tasks.keys()):
            self._cleanup_task(name)

    # ==================================================
    # HEARTBEAT
    # ==================================================
    def register_heartbeat(self, name: str, timeout: float):
        self._heartbeats[name] = time.time()
        self._heartbeat_timeout[name] = timeout

    def beat(self, name: str):
        self._heartbeats[name] = time.time()

    # ==================================================
    # ADMIN NOTIFY
    # ==================================================
    async def _notify_admin(self, task_name: str, message: str):
        if not self.client:
            return

        now = time.time()
        last = self._last_notify.get(task_name, 0)

        if now - last < self._notify_cooldown:
            return

        self._last_notify[task_name] = now

        try:
            await notify_admin_error(self.client, message)
        except Exception as e:
            log.warning("❌ Notify admin gagal: %s", e)
