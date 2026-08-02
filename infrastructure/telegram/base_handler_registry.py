import inspect
import time

from typing import Callable, Optional

from pyrogram import Client

from configs.logging_setup import log


class BaseHandlerRegistry:
    """
    Registry handler universal untuk bot Pyrogram.

    Fitur:
    - Validasi signature register & shutdown
    - Register handler berurutan
    - Optional shutdown hook (reverse order)
    - Tanpa IO / blocking
    """

    __slots__ = ("bot_name", "_handlers")

    def __init__(self, bot_name: str):
        self.bot_name = bot_name
        self._handlers: list[
            tuple[str, Callable[[Client], None], Optional[Callable[[Client], None]]]
        ] = []

    # ==================================================
    # ADD HANDLER
    # ==================================================
    def add(
        self,
        name: str,
        register: Callable[[Client], None],
        shutdown: Callable[[Client], None] | None = None,
    ) -> None:
        self._validate_register(register)
        if shutdown:
            self._validate_shutdown(shutdown)

        self._handlers.append((name, register, shutdown))

    # ==================================================
    # REGISTER ALL
    # ==================================================
    def register_all(self, app: Client) -> None:
        start = time.perf_counter()
        success = failed = 0

        for name, register, _ in self._handlers:
            try:
                register(app)
                success += 1
            except Exception:
                failed += 1
                log.exception(
                    "[%s] ❌ Handler '%s' gagal didaftarkan",
                    self.bot_name,
                    name,
                )

        duration = time.perf_counter() - start
        # log.info(
        #     "[%s] 🧩 Handler registered | success=%d failed=%d (%.2fs)",
        #     self.bot_name,
        #     success,
        #     failed,
        #     duration,
        # )

    # ==================================================
    # SHUTDOWN ALL (OPTIONAL)
    # ==================================================
    def shutdown_all(self, app: Client) -> None:
        """
        Dipanggil saat shutdown sistem.
        Dieksekusi TERBALIK dari urutan register.
        """
        log.info("[%s] 🔻 Shutdown handler dimulai", self.bot_name)

        for name, _, shutdown in reversed(self._handlers):
            if not shutdown:
                continue

            try:
                shutdown(app)
                log.info("[%s] 🧹 Handler '%s' dimatikan", self.bot_name, name)
            except Exception:
                log.exception(
                    "[%s] ❌ Gagal shutdown handler '%s'",
                    self.bot_name,
                    name,
                )

    # ==================================================
    # VALIDATION
    # ==================================================
    @staticmethod
    def _validate_register(func: Callable) -> None:
        sig = inspect.signature(func)
        if len(sig.parameters) != 1:
            raise TypeError(f"{func.__name__} harus memiliki signature (app: Client)")

    @staticmethod
    def _validate_shutdown(func: Callable) -> None:
        sig = inspect.signature(func)
        if len(sig.parameters) != 1:
            raise TypeError(
                f"{func.__name__} shutdown harus memiliki signature (app: Client)"
            )
