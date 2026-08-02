from pyrogram import Client

from shared.utils.admin_cache import AdminCache
from configs.logging_setup import log


def register_drac1n_handlers(app: Client, admin_cache: AdminCache) -> None:
    from .register_user import register_user_cmd_handlers
    from .register_admin import register_admin_handlers
    from .register_callbacks import register_callback_handlers

    register_callback_handlers(app)
    register_admin_handlers(app)
    register_user_cmd_handlers(app, admin_cache)

    # log.info("🎉 Semua handler drac1n_bot berhasil didaftarkan.")
