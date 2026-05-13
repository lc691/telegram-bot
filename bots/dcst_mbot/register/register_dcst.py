from pyrogram import Client

from bots.base_handler_registry import BaseHandlerRegistry
from configs.logging_setup import log


def register_dcst_handlers(app: Client, admin_cache=None) -> None:
    """
    Register handler untuk bot DCST (bot kelola channel).
    - WAJIB cepat
    - TIDAK BOLEH blocking
    - TIDAK BOLEH IO berat
    """

    _ = admin_cache  # kontrak konsisten, tidak dipakai

    registry = BaseHandlerRegistry("dcst_mbot")

    # ==================================================
    # LAZY IMPORT HANDLERS (ANTI HEAVY STARTUP)
    # ==================================================
    from ..delivery.telegram.forwarded.forwarded_message_handler import (
        register_forwarded_message_handler,
    )
    from ..delivery.telegram.repost.repost_handler import register_repost_handler
    from bots.dramaglow_bot.callback.handler_all_callback import (
        register_all_callbacks,
    )

    # ==================================================
    # REGISTER HANDLERS (SYSTEM FLOW ORDER)
    # ==================================================
    registry.add("callback_admin", register_all_callbacks)
    registry.add("forward_message", register_forwarded_message_handler)
    registry.add("repost", register_repost_handler)

    # ==================================================
    # APPLY TO APP
    # ==================================================
    registry.register_all(app)
    log.info("🎉 Semua handler bot kelola (dcst_mbot) berhasil didaftarkan.")
