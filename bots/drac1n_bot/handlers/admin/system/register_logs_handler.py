import asyncio

from pyrogram import Client, filters
from pyrogram.types import Message

from bots.drac1n_bot.decorators.admin_only import admin_only


def register_logs_handler(app: Client):

    @app.on_message(filters.command("logs"))
    @admin_only()
    async def logs_handler(_, message: Message):

        status = await message.reply_text(
            "📄 Mengambil log..."
        )

        try:
            process = await asyncio.create_subprocess_exec(
                "journalctl",
                "-u",
                "telegram-bot",
                "-n",
                "50",
                "--no-pager",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await process.communicate()

            if stderr:
                await status.edit_text(
                    f"❌ Error:\n<code>{stderr.decode()}</code>"
                )
                return

            logs = stdout.decode()

            if not logs.strip():
                logs = "Tidak ada log."

            if len(logs) > 4000:
                logs = logs[-4000:]

            await status.edit_text(
                f"<pre>{logs}</pre>"
            )

        except Exception as e:
            await status.edit_text(
                f"❌ Error:\n<code>{e}</code>"
            )