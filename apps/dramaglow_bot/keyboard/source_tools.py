from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from configs.logging_setup import log


def generate_source_markup() -> InlineKeyboardMarkup:
    """Markup untuk halaman utama 'request_menu' (source management)."""
    keyboard = [
        [
            InlineKeyboardButton(
                "📃 Lihat Semua Source", callback_data="admin_source_list_page_1"
            ),
            InlineKeyboardButton("➕ Tambah Source", callback_data="admin_add_source"),
        ],
        [
            InlineKeyboardButton(
                "❌ Hapus Source", callback_data="admin_delete_source_page_1"
            ),
            InlineKeyboardButton("↩️ Kembali", callback_data="admin_request_menu"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from apps.dramaglow_bot.repository.source_repository import (
    count_all_request_sources,
    count_sources,
    get_all_request_sources,
)
from configs.logging_setup import log


def build_source_list_keyboard(
    page: int = 1, per_page: int = 5
) -> InlineKeyboardMarkup:
    total_items = count_sources()
    total_pages = max((total_items + per_page - 1) // per_page, 1)
    page = max(1, min(page, total_pages))
    offset = (page - 1) * per_page

    sources = get_all_request_sources(offset=offset, limit=per_page)

    buttons = [
        [InlineKeyboardButton(text=label, callback_data=f"request_source:{code}")]
        for code, label in sources
    ]

    nav_buttons = []

    if page > 1:
        nav_buttons.append(
            InlineKeyboardButton(
                "⬅️ Prev", callback_data=f"request_source_page:{page - 1}"
            )
        )

    nav_buttons.append(
        InlineKeyboardButton(f"📄 {page}/{total_pages}", callback_data="noop")
    )

    if page < total_pages:
        nav_buttons.append(
            InlineKeyboardButton(
                "➡️ Next", callback_data=f"request_source_page:{page + 1}"
            )
        )

    if nav_buttons:
        buttons.append(nav_buttons)

    # Tambahkan tombol batal
    buttons.append(
        [InlineKeyboardButton("❌ Batal", callback_data="cancel_request_fsm")]
    )

    log.info(f"[PAGINATION] Membuka halaman {page} dengan {len(buttons)} tombol")
    log.info(
        f"[DEBUG] total_items={total_items}, offset={offset}, per_page={per_page}, sources_returned={len(sources)}"
    )

    return InlineKeyboardMarkup(buttons)
