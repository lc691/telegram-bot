from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def vip_stats_keyboard(
    source: str, jenis: str, page: int, max_page: int
) -> InlineKeyboardMarkup:
    # Navigasi halaman
    nav_buttons = []
    if page > 0:
        nav_buttons.append(
            InlineKeyboardButton(
                "⬅️ Sebelumnya", callback_data=f"vip_stats:{source}:{jenis}:{page - 1}"
            )
        )
    if page < max_page:
        nav_buttons.append(
            InlineKeyboardButton(
                "Berikutnya ➡️", callback_data=f"vip_stats:{source}:{jenis}:{page + 1}"
            )
        )

    # Tombol switch antar jenis data
    switch_buttons = [
        InlineKeyboardButton("👑 VIP", callback_data=f"vip_stats:{source}:vip:0"),
        InlineKeyboardButton(
            "💰 Donasi", callback_data=f"vip_stats:{source}:donation:0"
        ),
    ]

    # Tombol filter status (jika jenis == 'vip' atau dimulai dengan 'vip-')
    filter_buttons = []
    if jenis == "vip" or jenis.startswith("vip-"):
        filter_buttons = [
            [
                InlineKeyboardButton(
                    "✅ Aktif", callback_data=f"vip_stats:{source}:vip-active:0"
                ),
                InlineKeyboardButton(
                    "⚠️ Hampir Habis", callback_data=f"vip_stats:{source}:vip-soon:0"
                ),
                InlineKeyboardButton(
                    "❌ Kadaluarsa", callback_data=f"vip_stats:{source}:vip-expired:0"
                ),
            ],
        ]

    # Info halaman & tombol kembali
    page_info = InlineKeyboardButton(
        f"📄 Halaman {page + 1}/{max_page + 1}", callback_data="noop"
    )
    back_button = InlineKeyboardButton("↩️ Kembali", callback_data="vip_tools_menu")

    # Susun layout keyboard
    keyboard = []
    if filter_buttons:
        keyboard.extend(filter_buttons)  # ✅ perbaikan utama di sini
    keyboard.append(switch_buttons)
    if nav_buttons:
        keyboard.append(nav_buttons)
    keyboard.append([page_info])
    keyboard.append([back_button])

    return InlineKeyboardMarkup(keyboard)
