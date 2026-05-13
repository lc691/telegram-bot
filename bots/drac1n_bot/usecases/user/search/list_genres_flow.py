from pyrogram import Client
from pyrogram.enums import ParseMode
from pyrogram.types import Message

from configs.logging_setup import log
from ....repository.genre_repository import fetch_all_genres
from ....presenters.user.search.genre_keyboard import build_genre_keyboard


async def show_genre_list(client: Client, message: Message):
    log.info(
        "[GENRE] Request list genre chat_id=%s user_id=%s",
        message.chat.id,
        message.from_user.id if message.from_user else None,
    )

    genres = fetch_all_genres()

    log.info("[GENRE] Genre ditemukan: %d", len(genres))

    keyboard = build_genre_keyboard(genres)
    if not keyboard:
        await message.reply("🙅 Tidak ada genre ditemukan.")
        return

    await message.reply(
        "📂 <b>Pilih Genre:</b>",
        reply_markup=keyboard,
        parse_mode=ParseMode.HTML,
    )

    log.info("[GENRE] Genre list sent chat_id=%s", message.chat.id)
