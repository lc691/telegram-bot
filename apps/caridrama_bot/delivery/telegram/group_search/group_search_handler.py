from pyrogram import Client, filters
from pyrogram.enums import ParseMode
from pyrogram.types import Message

from configs.logging_setup import log
from shared.texts.get_no_text_message import get_no_text_message

from ....usecases.group_search.group_search_flow import (
    run_group_search_flow,
)
from ....presenters.group_search_presenter import (
    build_result_keyboard,
)
from ....utils.telegram_safe import safe_edit
from ..guards.guards_police import (
    allow_groups_chats,
)


def register_response_handler(app: Client):

    @app.on_message(filters.group & filters.text, group=-1)
    async def group_search_handler(client: Client, message: Message):
        if not await allow_groups_chats(client, message):
            return

        text = (message.text or "").strip()
        if not text:
            await message.reply(
                f"{get_no_text_message()}",
                parse_mode=ParseMode.HTML,
            )
            return

        result = await run_group_search_flow(
            text=text,
            user_id=message.from_user.id,
        )

        if not result:
            return

        if result.get("error") == "forbidden":
            await message.reply(
                "🚫 Permintaan kamu mengandung kata terlarang."
            )
            return

        if result.get("error") == "cooldown":
            await message.reply(
                "⏳ Tunggu sebentar sebelum mencari lagi."
            )
            return

        if result.get("error") == "empty":
            await message.reply(
                f"❗ Setelah <b>{result['trigger']}</b>, tulis judul.",
                parse_mode=ParseMode.HTML,
            )
            return

        query = result["query"]
        shows = result["results"]

        searching_msg = await message.reply(
            f"🔍 Hasil pencarian untuk: <b>{query}</b>",
            parse_mode=ParseMode.HTML,
        )

        if not shows:
            await safe_edit(
                searching_msg,
                f"📭 Tidak ditemukan hasil untuk <b>{query}</b>.",
                parse_mode=ParseMode.HTML,
            )
            return

        await safe_edit(
            searching_msg,
            f"🔍 Hasil pencarian untuk: <b>{query}</b>",
            reply_markup=build_result_keyboard(shows),
            parse_mode=ParseMode.HTML,
        )
