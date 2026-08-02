from bots.bot_shutdown_sequence import shutdown_sequence
from bots.bot_startup_sequence import startup_sequence
from common.utils.admin_cache import admin_cache
from configs.logging_setup import log


class BotManager:
    """
    Bertanggung jawab atas lifecycle 1 bot Telegram:
    - create app
    - startup (polling)
    - register handler
    - shutdown

    ❗ Tidak mengurus webhook / HTTP
    """

    __slots__ = (
        "name",
        "factory",
        "handler_register_func",
        "startup_func",
        "app",
        "_started",
    )

    def __init__(self, name, factory, handler_register_func, startup_func=None):
        self.name = name
        self.factory = factory
        self.handler_register_func = handler_register_func
        self.startup_func = startup_func

        self.app = None
        self._started = False

    async def initialize(self) -> bool:
        """
        Start bot sekali saja (idempotent).
        Dipanggil oleh main orchestrator.
        """
        if self._started:
            log.debug("Bot %s already started, skip", self.name)
            return True

        try:
            # 1️⃣ Create Telegram app (client, dispatcher, dll)
            app = await self.factory()
            if not app:
                log.error("Bot factory returned None: %s", self.name)
                return False

            self.app = app

            # 2️⃣ Custom startup (optional, bot-specific)
            if self.startup_func:
                await self.startup_func(app)

            # 3️⃣ Core startup sequence (polling, middleware, dsb)
            await startup_sequence(app, self.name)

            # 4️⃣ Register handlers (reuse cache)
            self.handler_register_func(app, admin_cache)

            self._started = True
            log.info("[%s] started successfully", self.name)
            return True

        except Exception:
            log.exception("Bot init failed: %s", self.name)
            return False

    async def shutdown(self) -> None:
        """
        Shutdown bot dengan rapi.
        """
        if not self.app or not self._started:
            return

        log.info("Shutting down bot %s", self.name)
        await shutdown_sequence(self.app, self.name)
        self._started = False
