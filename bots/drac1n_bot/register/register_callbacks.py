# register/register_callbacks.py
from pyrogram import Client
from bots.base_handler_registry import BaseHandlerRegistry
from configs.logging_setup import log


def register_callback_handlers(app: Client) -> None:
    registry = BaseHandlerRegistry("drac1n_bot")

    from ..callback.handler_all_callback import register_all_callbacks

    registry.add("callback_admin", register_all_callbacks)
    registry.register_all(app)

    # log.info("🎉 Callback handlers drac1n_bot didaftarkan.")
