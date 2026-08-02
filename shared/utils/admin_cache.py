import asyncio
import traceback

from typing import Any, Callable, Coroutine, List, Optional

from infrastructure.telegram.bots_registry import get_bot
from shared.utils.admin_notifier import notify_admin_error
from configs.logging_setup import log
from database.repositories.admin.admin_utils import load_admin_ids


class AdminCache:
    def __init__(self, reload_interval: int = 300):
        self._admin_ids: List[int] = []
        self._super_admin_ids: List[int] = []

        self._reload_interval = reload_interval
        self._callbacks: List[
            Callable[[List[int]], Coroutine[Any, Any, None]]
        ] = []
        self._callbacks_registered = False

        self._lock = asyncio.Lock()
        self._task: Optional[asyncio.Task] = None
        self._stop_event = asyncio.Event()

    # ==================================================
    # BASIC API
    # ==================================================

    def __contains__(self, user_id: int) -> bool:
        return user_id in self._admin_ids

    @property
    def admin_ids(self) -> List[int]:
        return self._admin_ids.copy()

    def is_admin(self, user_id: int) -> bool:
        return user_id in self._admin_ids

    def is_super_admin(self, user_id: int) -> bool:
        return user_id in self._super_admin_ids

    def set_super_admins(self, ids: List[int]) -> None:
        self._super_admin_ids = ids
        log.info("🔐 Super admin diupdate: %s", ids)

    # ==================================================
    # CALLBACKS
    # ==================================================

    def register_callback(
        self,
        cb: Callable[[List[int]], Coroutine[Any, Any, None]],
    ) -> None:
        if self._callbacks_registered:
            return
        self._callbacks.append(cb)
        self._callbacks_registered = True

    async def _notify_callbacks(self, admin_ids: List[int]) -> None:
        for cb in self._callbacks:
            try:
                await cb(admin_ids)
            except Exception:
                log.error(
                    "❌ Callback '%s' error:\n%s",
                    cb.__name__,
                    traceback.format_exc(),
                )

    # ==================================================
    # LOAD / RELOAD
    # ==================================================

    async def force_reload(self) -> None:
        await self._reload_admin_ids()

    async def _reload_admin_ids(self) -> None:
        async with self._lock:
            new_ids = list(await asyncio.to_thread(load_admin_ids))

            if set(new_ids) == set(self._admin_ids):
                log.debug("Admin IDs tidak berubah.")
                return

            self._admin_ids = new_ids
            # log.info("✅ Admin IDs diperbarui: %s", self._admin_ids)

        # ⚠️ CALLBACK DI LUAR LOCK
        await self._notify_callbacks(self.admin_ids)

    async def get_admin_ids(self) -> set[int]:
        if not self._admin_ids:
            await self.force_reload()
        return set(self._admin_ids)

    # ==================================================
    # BACKGROUND TASK
    # ==================================================

    async def _periodic_reload_loop(self) -> None:
        # log.info("⏳ Reload admin IDs periodik dimulai.")
        await asyncio.sleep(2)

        while not self._stop_event.is_set():
            try:
                await self._reload_admin_ids()
            except Exception as e:
                msg = f"❌ Reload admin IDs gagal:\n{e}"
                log.error(msg, exc_info=True)
                await self._notify_admin_error(msg)

            await asyncio.sleep(self._reload_interval)

    def start_background_task(self) -> None:
        if self._task and not self._task.done():
            return

        self._stop_event.clear()
        self._task = asyncio.create_task(
            self._periodic_reload_loop(),
            name="admin-cache-reload",
        )
        # log.info("🟢 AdminCache background task dimulai.")

    async def stop(self) -> None:
        self._stop_event.set()

        if self._task:
            self._task.cancel()
            with asyncio.suppress(asyncio.CancelledError):
                await self._task

        self._task = None
        log.info("🧹 AdminCache background task dihentikan.")

    # ==================================================
    # ERROR NOTIFY
    # ==================================================

    async def _notify_admin_error(self, message: str) -> None:
        try:
            bot = get_bot(next(iter(get_bot.__globals__["_bots"]), None))
            if bot:
                await notify_admin_error(bot, message)
        except Exception as e:
            log.warning("❌ Gagal kirim notifikasi admin: %s", e)


# ==================================================
# GLOBAL INSTANCE
# ==================================================
admin_cache = AdminCache()
