# preview.py
from pyrogram import Client
from pyrogram.enums import ParseMode
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from bots.dramaglow_bot.handlers.admin.broadcast.broadcast_cache import (
    set_broadcast_text,
)
from common.utils.admin_cache import admin_cache


async def preview_broadcast(client: Client, message: Message, broadcast_text: str):
    user_id = message.from_user.id

    # Cek admin manual
    is_admin = await admin_cache.is_admin_async(user_id)
    if not is_admin:
        await message.reply_text("⛔️ Akses ditolak. Fitur ini hanya untuk admin.")
        return

    # Simpan teks broadcast ke cache per user_id
    set_broadcast_text(user_id, broadcast_text)

    # Kirim preview dengan tombol konfirmasi
    await message.reply_text(
        f"📢 <b>Preview Broadcast:</b>\n\n{broadcast_text}\n\n"
        "✅ Apakah kamu ingin mengirim broadcast ini ke semua user?",
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
        quote=True,
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("✅ Kirim", callback_data="broadcast_confirm")],
                [InlineKeyboardButton("❌ Batal", callback_data="broadcast_cancel")],
            ]
        ),
    )
