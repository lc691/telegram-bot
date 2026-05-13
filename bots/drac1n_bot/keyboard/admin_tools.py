from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from configs.logging_setup import log


def generate_admin_tools_markup() -> InlineKeyboardMarkup:
    """Generate markup untuk menu Admin Tools."""
    try:
        keyboard = [
            [
                InlineKeyboardButton(
                    "📄 Daftar Admin", callback_data="admin_list_start"
                ),
                InlineKeyboardButton("🔁 Update", callback_data="admin_update_start"),
            ],
            [
                InlineKeyboardButton("➕ Tambah", callback_data="admin_add_start"),
                InlineKeyboardButton("🗑️ Hapus", callback_data="admin_remove_start"),
            ],
            [InlineKeyboardButton("⬅️ Kembali ke Dashboard", callback_data="dashboard")],
        ]
        return InlineKeyboardMarkup(keyboard)

    except Exception as e:
        log.error("[MARKUP] Gagal generate admin tools markup: %s", e, exc_info=True)
        return InlineKeyboardMarkup([])  # fallback aman


def generate_add_admin_confirm_buttons(admin_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "✅ Ya", callback_data=f"admin_add_confirm_yes_{admin_id}"
                ),
                InlineKeyboardButton(
                    "❌ Tidak", callback_data=f"admin_add_confirm_no_{admin_id}"
                ),
            ]
        ]
    )


def generate_admin_remove_confirm_buttons(admin_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "✅ Ya", callback_data=f"confirm_remove_admin_{admin_id}"
                ),
                InlineKeyboardButton(
                    "❌ Tidak", callback_data=f"cancel_remove_admin_{admin_id}"
                ),
            ]
        ]
    )


def generate_admin_list_markup(admins, page=0, per_page=5):
    try:
        start = page * per_page
        end = start + per_page
        subset = admins[start:end]

        total_pages = (len(admins) + per_page - 1) // per_page

        # ✅ Inisialisasi lebih awal
        buttons = []

        # Tombol info halaman
        buttons.append(
            [
                InlineKeyboardButton(
                    f"📄 Page {page + 1}/{total_pages}", callback_data="noop"
                )
            ]
        )

        for admin in subset:
            name = admin.get("first_name", "Unknown")
            username = admin.get("username")
            label = f"{name} (@{username})" if username else name
            buttons.append(
                [
                    InlineKeyboardButton(
                        text=label,
                        callback_data=f"admin_detail_{admin.get('user_id', '')}",
                    )
                ]
            )

        # Tombol navigasi (Prev dan Next)
        nav_buttons = []
        if page > 0:
            nav_buttons.append(
                InlineKeyboardButton("⬅️ Prev", callback_data=f"admin_page_{page - 1}")
            )
        if end < len(admins):
            nav_buttons.append(
                InlineKeyboardButton("Next ➡️", callback_data=f"admin_page_{page + 1}")
            )

        if nav_buttons:
            buttons.append(nav_buttons)

        # Tombol kembali
        buttons.append(
            [InlineKeyboardButton("🔙 Kembali", callback_data="admin_tools_menu")]
        )

        return InlineKeyboardMarkup(buttons)
    except Exception as e:
        log.error(f"Error generating admin list markup: {e}", exc_info=True)
        return None
