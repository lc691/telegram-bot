from pyrogram import Client, filters

from ..feedback_command_handler import feedback_command_handler

FEEDBACK_GROUP = 13


def register_feedback_cmd_handler(app: Client) -> None:
    @app.on_message(
        filters.private
        & filters.command(["masukan", "feedback"]),
        group=FEEDBACK_GROUP,
    )
    async def feedback_command(client: Client, message) -> None:
        await feedback_command_handler(client, message)