from pyrogram.enums import ParseMode
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from ..services.greeting import (
    get_country_code_by_language,
    get_greeting_by_country,
)


async def show_main_menu(client, message, display_name: str = None):
    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("▶️ Mulai Menonton", url="https://t.me/dracinshort")],
            [InlineKeyboardButton("💎 Beli VIP", callback_data="vip_menu")],
            [InlineKeyboardButton("📊 Cek Status", callback_data="vip_status")],
        ]
    )

    language_code = getattr(message.from_user, "language_code", "id")
    country_code = get_country_code_by_language(language_code)
    greeting = get_greeting_by_country(country_code)

    user_name = display_name or getattr(message.from_user, "first_name", "User")

    welcome_text = (
        f"👋 {greeting}, <b>{user_name}</b>!\n"
        f"🏮 Selamat datang di <b>DCSTV • Short Drama</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🎬 Kisah singkat penuh emosi & takdir setiap hari!\n"
        f"🌸 Update rutin, serasa nonton drama langsung di istana~\n\n"
        f"❓ <b>Butuh bantuan?</b>\n"
        f"👤 Admin: @mimindcstv | @admischelia\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📌 <b>Pilih tombol di bawah untuk membuka kisahmu:</b>"
    )

    await message.reply_text(
        welcome_text,
        reply_markup=keyboard,
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
    )
