from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup


async def show_main_menu(client, message, display_name: str):
    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("🔍 Cari Film", callback_data="main_search"),
                InlineKeyboardButton("📥 Request", callback_data="main_request"),
            ],
            [InlineKeyboardButton("💎 VIP", callback_data="main_vip")],
        ]
    )

    await message.reply_text(
        f"👋 Hai <b>{display_name}</b>!\n\n"
        "Selamat datang di bot Drac1n 🌟.\n"
        "Silakan pilih menu di bawah ini untuk mulai.",
        reply_markup=keyboard,
        parse_mode="HTML",
    )
