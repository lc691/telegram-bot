from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def generate_stats_markup() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("📊 Top Film", callback_data="stat_top_films")],
        [InlineKeyboardButton("👤 User Aktif", callback_data="stat_top_users")],
        [
            InlineKeyboardButton(
                "💎 View VIP vs Gratis", callback_data="stat_vip_vs_free"
            )
        ],
        [InlineKeyboardButton("🎬 Detail Film", callback_data="stat_detail_menu")],
        [InlineKeyboardButton("⬅️ Kembali", callback_data="dashboard")],
    ]
    return InlineKeyboardMarkup(keyboard)
