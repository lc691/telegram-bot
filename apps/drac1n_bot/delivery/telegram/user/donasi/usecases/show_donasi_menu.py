from pyrogram import Client
from pyrogram.enums import ParseMode
from pyrogram.types import Message

from configs.logging_setup import log

from apps.drac1n_bot.delivery.telegram.user.donasi.presenters.donasi_keyboard import build_donasi_keyboard
from apps.drac1n_bot.delivery.telegram.user.donasi.presenters.donasi_text import donasi_intro_text


async def show_donasi_menu(client: Client, message: Message):
    user_id = message.from_user.id if message.from_user else None

    log.info("[DONASI] Open menu user_id=%s", user_id)

    await message.reply_text(
        donasi_intro_text(),
        reply_markup=build_donasi_keyboard(),
        parse_mode=ParseMode.HTML,
    )
