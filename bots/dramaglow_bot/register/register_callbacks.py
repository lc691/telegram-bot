# register/register_callbacks.py
from pyrogram import Client
from bots.base_handler_registry import BaseHandlerRegistry
from configs.logging_setup import log


def register_callback_handlers(app: Client) -> None:
    registry = BaseHandlerRegistry("dramaglow_bot")

    from ..callback.handler_all_callback import register_all_callbacks

    registry.add("callback_admin", register_all_callbacks)
    registry.register_all(app)

    # log.info("🎉 Callback handlers dramaglow_bot didaftarkan.")
