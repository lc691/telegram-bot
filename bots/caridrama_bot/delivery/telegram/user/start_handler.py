from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def register_start_handler(app: Client):
    @app.on_message(filters.command("start") | filters.command("cari"))
    async def start_handler(client, message):
        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "🔍 Cari Drama", switch_inline_query_current_chat=""
                    )
                ]
            ]
        )

        await message.reply_text(
            "📺 Mau cari drama? Klik tombol di bawah ini:", reply_markup=keyboard
        )
