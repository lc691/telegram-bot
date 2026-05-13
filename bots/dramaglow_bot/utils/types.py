from dataclasses import dataclass

from pyrogram.types import InlineKeyboardMarkup


@dataclass
class MessageUpdate:
    text: str
    reply_markup: InlineKeyboardMarkup
