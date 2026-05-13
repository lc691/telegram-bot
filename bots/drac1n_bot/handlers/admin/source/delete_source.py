from pyrogram import Client
from pyrogram.enums import ParseMode
from pyrogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from bots.drac1n_bot.repository.source_repository import count_sources, get_sources

ITEMS_PER_PAGE = 5


async def admin_delete_source_list_callback(
    client: Client, callback_query: CallbackQuery, state=None
):
    data = callback_query.data
    page = 1

    if data.startswith("admin_delete_source_page_"):
        try:
            page = int(data.split("_")[-1])
        except ValueError:
            page = 1

    offset = (page - 1) * ITEMS_PER_PAGE
    sources = get_sources(offset=offset, limit=ITEMS_PER_PAGE)
    total_sources = count_sources()
    total_pages = (total_sources + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE

    if not sources:
        await callback_query.answer("Tidak ada source ditemukan.", show_alert=True)
        return

    text_lines = ["🗑 <b>Hapus Source</b>\nKlik tombol di bawah untuk menghapus:"]
    markup_rows = []

    for src in sources:
        text_lines.append(f"🔹 <b>{src['code']}</b> — {src['label']}")
        markup_rows.append(
            [
                InlineKeyboardButton(
                    f"🗑 Hapus {src['code']}",
                    callback_data=f"admin_delete_confirm_{src['id']}",
                )
            ]
        )

    # Pagination buttons
    buttons = []

    if page > 1:
        buttons.append(
            InlineKeyboardButton(
                "⬅️ Prev", callback_data=f"admin_delete_source_page_{page-1}"
            )
        )
    if page < total_pages:
        buttons.append(
            InlineKeyboardButton(
                "Next ➡️", callback_data=f"admin_delete_source_page_{page+1}"
            )
        )

    if buttons:
        markup_rows.append(buttons)

    markup_rows.append(
        [InlineKeyboardButton("↩️ Kembali", callback_data="request_menu")]
    )

    markup = InlineKeyboardMarkup(markup_rows)

    await callback_query.message.edit_text(
        "\n".join(text_lines),
        reply_markup=markup,
        parse_mode=ParseMode.HTML,
    )
