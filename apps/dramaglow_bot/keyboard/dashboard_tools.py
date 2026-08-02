from pyrogram import Client
from pyrogram.enums import ParseMode
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from configs.logging_setup import log

# Struktur tombol dashboard
DASHBOARD_BUTTONS = [
    [("👤 Admin Tools", "admin_tools_menu"), ("🌟 VIP Tools", "vip_tools_menu")],
    [("📡 Channel Tools", "channel_menu"), ("👥 Daftar Pengguna", "list_users")],
    [("🎬 Request Film", "request_menu"), ("📈 Statistik", "show_stats")],
    [("🔄 Refresh", "refresh_dashboard")],
    [("🚪 Tutup", "close")],
]


def generate_dashboard_markup() -> InlineKeyboardMarkup:
    """Membangun InlineKeyboardMarkup untuk dashboard utama."""
    try:
        keyboard = []
        for row in DASHBOARD_BUTTONS:
            keyboard_row = [
                InlineKeyboardButton(text=text, callback_data=data)
                for text, data in row
            ]
            keyboard.append(keyboard_row)

        return InlineKeyboardMarkup(keyboard)

    except Exception as e:
        log.error("[Dashboard UI] ❌ Gagal membuat markup: %s", e, exc_info=True)
        # Fallback minimal
        return InlineKeyboardMarkup(
            [[InlineKeyboardButton("🚪 Tutup", callback_data="close")]]
        )


async def show_dashboard(client: Client, message: Message):
    """Menampilkan dashboard awal (tanpa statistik atau informasi tambahan)."""
    markup = generate_dashboard_markup()
    try:
        await message.reply_text(
            text="📊 <b>Dashboard Utama</b>",
            reply_markup=markup,
            parse_mode=ParseMode.HTML,
        )
    except Exception as e:
        log.error("[Dashboard UI] ❌ Gagal mengirim dashboard: %s", e, exc_info=True)
