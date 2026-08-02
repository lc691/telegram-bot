from pyrogram import Client
from pyrogram.enums import ParseMode
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from pyrogram.types import Message

from .menu_config import build_feedback_keyboard
from .text_template import FEEDBACK_TEXT


async def feedback_command_handler(
    client: Client,
    message: Message,
) -> None:
    await message.reply_text(
        text=FEEDBACK_TEXT,
        parse_mode=ParseMode.HTML,
        reply_markup=build_feedback_keyboard(),
        disable_web_page_preview=True,
    )


