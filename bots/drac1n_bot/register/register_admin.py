# register/register_admin.py
from pyrogram import Client
from bots.base_handler_registry import BaseHandlerRegistry
from configs.logging_setup import log


def register_admin_handlers(app: Client) -> None:
    registry = BaseHandlerRegistry("drac1n_bot")

    from ..handlers.admin.broadcast.admin_broadcast import (
        register_broadcast_message_handlers,
    )
    from ..handlers.admin.users.handler_list_user import register_list_user_handlers
    from ..delivery.telegram.admin.channel.handler_channel import (
        register_channel_handlers,
    )
    from ..delivery.telegram.admin.file.new_file_command_handler import (
        register_new_file_handler,
    )
    from ..delivery.telegram.admin.inspect.admin_inspect_command import (
        register_inspect_cmd_handler,
    )
    from ..delivery.telegram.admin.posting.posting_command_handler import (
        register_posting_handler,
    )
    from ..delivery.telegram.admin.thumbnile.thumbnile_command_handler import (
        register_thumbnail_handler,
    )
    from ..delivery.telegram.admin.voucher.voucher_command_handler import (
        register_voucher_command_handler,
    )

    from ..delivery.telegram.admin.leaderboard.handlers.register import (
        register_leaderboard,
    )

    registry.add("broadcast", register_broadcast_message_handlers)
    registry.add("list_user", register_list_user_handlers)
    registry.add("channel", register_channel_handlers)
    registry.add("file", register_new_file_handler)
    registry.add("inspect", register_inspect_cmd_handler)
    registry.add("posting", register_posting_handler)
    registry.add("thumbnile", register_thumbnail_handler)
    registry.add("voucher", register_voucher_command_handler)
    registry.add("leaderboard", register_leaderboard)
    registry.register_all(app)
    log.info("🎉 Admin handlers drac1n_bot didaftarkan.")
