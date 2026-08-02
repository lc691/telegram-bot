import subprocess

from pyrogram import Client, filters
from pyrogram.types import Message

from configs.logging_setup import log
from bots.drac1n_bot.decorators.admin_only import admin_only


SERVICE_NAME = "telegram-bot"


def register_restart_service_handler(app: Client):

    @app.on_message(filters.command("restart"))
    @admin_only()
    async def restart_service(_, message: Message):

        await message.reply_text(
            "🔄 Restarting service..."
        )

        try:
            subprocess.Popen(
                [
                    "sudo",
                    "/usr/local/bin/restart-bot.sh"
                ]
            )

        except Exception as e:
            log.exception(e)

            await message.reply_text(
                f"❌ Failed:\n<code>{e}</code>"
            )