from pyrogram import Client
from pyrogram.types import Message


class TelegramSender:
    def __init__(self, app: Client):
        self._app = app

    async def send_message(
        self,
        *,
        chat_id: int,
        text: str,
        disable_web_page_preview: bool = True,
    ) -> Message:
        return await self._app.send_message(
            chat_id=chat_id,
            text=text,
            disable_web_page_preview=disable_web_page_preview,
        )

    async def send_photo(
        self,
        *,
        chat_id: int,
        photo,
        caption: str | None = None,
    ) -> Message:
        return await self._app.send_photo(
            chat_id=chat_id,
            photo=photo,
            caption=caption,
        )

    async def send_document(
        self,
        *,
        chat_id: int,
        document,
        caption: str | None = None,
    ) -> Message:
        return await self._app.send_document(
            chat_id=chat_id,
            document=document,
            caption=caption,
        )