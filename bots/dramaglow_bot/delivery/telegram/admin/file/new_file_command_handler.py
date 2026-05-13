from pyrogram import Client, filters
from pyrogram.types import Message

from config import DB_DRAMA_GLOW
from configs.logging_setup import log

from .....usecases.admin.file.new_file_logic import process_new_file


NEW_FILE_GROUP = 7


def register_new_file_handler(app: Client):

    @app.on_message(
        filters.chat(DB_DRAMA_GLOW) & (filters.document | filters.video),
        group=NEW_FILE_GROUP,
    )
    async def handle_new_file(client: Client, message: Message):
        msg_id = message.id
        chat_id = message.chat.id

        log.info(
            "[NEW_FILE] incoming chat_id=%s msg_id=%s",
            chat_id,
            msg_id,
        )

        try:
            await process_new_file(client, message)

        except Exception:
            log.exception(
                "[NEW_FILE] failed chat_id=%s msg_id=%s",
                chat_id,
                msg_id,
            )
