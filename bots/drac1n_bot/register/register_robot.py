# register/register_callbacks.py
from pyrogram import Client
from bots.base_handler_registry import BaseHandlerRegistry
from configs.logging_setup import log


def register_callback_handlers(app: Client) -> None:
    registry = BaseHandlerRegistry("drac1n_bot")

    from ..delivery.telegram.robot.auto_comment_handler import (
        register_auto_comment_handler,
    )
    from ..delivery.telegram.robot.robot_welcome import register_welcome_handler

    registry.add("welcome", register_welcome_handler)
    registry.add("auto_comment", register_auto_comment_handler)
    registry.register_all(app)

    log.info("🎉 Callback handlers drac1n_bot didaftarkan.")
