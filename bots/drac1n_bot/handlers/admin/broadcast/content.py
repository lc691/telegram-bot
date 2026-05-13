from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

BROADCAST_TEXT = (
    "👋 Halo kakak-kakak semua... 😘\n\n"
    "Sekadar informasi, di @drac1n_bot sekarang sudah tersedia fitur <b>Cari Film</b>!\n\n"
    "🎬 Kamu bisa mencari judul film langsung di bot, tanpa harus scroll di channel atau grup.\n\n"
    "Cukup kirim perintah:\n"
    "<code>/cari judul_film</code>\n\n"
    "Selamat mencoba fitur baru ini! 😊✨"
)

BROADCAST_BUTTONS = InlineKeyboardMarkup(
    [
        [
            InlineKeyboardButton(
                "💎 Beli VIP Sekarang", url="https://t.me/dramaglow_bot?start=vip"
            )
        ],
        [InlineKeyboardButton("📣 Channel Utama", url="https://t.me/dramaglow")],
    ]
)
