from pyrogram import Client, filters
from pyrogram.types import Message

from .constants import DEFAULT_USER_GROUP, EXCLUDED_COMMANDS
from .message_entrypoint import message_entrypoint
from common.utils.event_tracer import EventTracer


def register_text_router_handler(app: Client):

    @app.on_message(
        filters.private
        & filters.text
        & ~filters.command(EXCLUDED_COMMANDS)
        & ~filters.me,
        group=DEFAULT_USER_GROUP,
    )
    async def private_handler(client: Client, message: Message):

        user_id = message.from_user.id if message.from_user else 0
        tracer = EventTracer(user_id)

        tracer.entry(message.text or "")
        tracer.handler("PRIVATE_ROUTER")

        await message_entrypoint(client, message)

        tracer.result("PRIVATE_DONE")


    @app.on_message(
        filters.group
        & filters.text
        & ~filters.command(EXCLUDED_COMMANDS)
        & ~filters.me,
        group=DEFAULT_USER_GROUP,
    )
    async def group_handler(client: Client, message: Message):

        user_id = message.from_user.id if message.from_user else 0
        tracer = EventTracer(user_id)

        tracer.entry(message.text or "")
        tracer.handler("GROUP_ROUTER")

        await message_entrypoint(client, message)

        tracer.result("GROUP_DONE")