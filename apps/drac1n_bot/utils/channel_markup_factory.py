from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def generate_channel_markup():
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "📋 Cek Status Channel", callback_data="check_channels"
                ),
                InlineKeyboardButton(
                    "📄 Daftar Channel", callback_data="list_required_channels"
                ),
            ],
            [
                InlineKeyboardButton(
                    "➕ Tambah Channel", callback_data="add_required_channel"
                )
            ],
            [InlineKeyboardButton("⬅️ Kembali ke Dashboard", callback_data="dashboard")],
        ]
    )


def generate_channel_list_markup(channels):
    keyboard = []
    for ch in channels:
        username = ch.get("username", "❓")
        keyboard.append(
            [
                InlineKeyboardButton(
                    f"❌ Hapus {username}", callback_data=f"delete_channel:{username}"
                )
            ]
        )
    keyboard.append(
        [
            InlineKeyboardButton(
                "➕ Tambah Channel", callback_data="add_required_channel"
            ),
            InlineKeyboardButton("⬅️ Kembali", callback_data="dashboard"),
        ]
    )
    return InlineKeyboardMarkup(keyboard)
