from pyrogram import Client

from bots.base_handler_registry import BaseHandlerRegistry
from common.utils.admin_cache import AdminCache
from configs.logging_setup import log


def register_user_cmd_handlers(app: Client, admin_cache: AdminCache) -> None:
    """
    Register semua user command handler drac1n_bot.
    - WAJIB cepat
    - TIDAK BOLEH blocking
    - TIDAK BOLEH IO berat
    """

    registry = BaseHandlerRegistry("drac1n_bot")

    # ==================================================
    # LAZY IMPORT HANDLERS (ANTI HEAVY STARTUP)
    # ==================================================

    from ..delivery.telegram.user.vip.handlers.register_vip import register_vip
    from ..delivery.telegram.user.refferral.handlers.register import register_referral
    from ..delivery.telegram.user.info.handlers.info_command_handler import (
        register_info_cmd_handler,
    )
    from ..delivery.telegram.user.inline_search.inline_search_handler import (
        register_inline_search,
    )

    from ..delivery.telegram.user.redeem.handlers.redeem_command_handler import (
        register_redeem_command_handler,
    )
    from ..delivery.telegram.user.start.handlers.start_command_handler import (
        register_start_cmd_handler,
    )
    from ..delivery.telegram.user.status.handlers.status_command_handler import (
        register_status_cmd_handler,
    )

    # ==================================================
    # REGISTER HANDLERS (USER FLOW ORDER)
    # ==================================================
    registry.add("start", lambda app: register_start_cmd_handler(app, admin_cache))
    registry.add("status", lambda app: register_status_cmd_handler(app, admin_cache))
    registry.add("info", register_info_cmd_handler)
    registry.add("inline", register_inline_search)

    registry.add("vip", register_vip)

    registry.add("redeem_voucher", register_redeem_command_handler)
    registry.add("referral_menu", register_referral)

    # ==================================================
    # APPLY TO APP
    # ==================================================
    registry.register_all(app)
    log.info("🎉 Semua handler user drac1n_bot berhasil didaftarkan.")
