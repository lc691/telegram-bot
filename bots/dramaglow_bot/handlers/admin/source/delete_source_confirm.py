from pyrogram import Client
from pyrogram.enums import ParseMode
from pyrogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from bots.dramaglow_bot.repository.source_repository import delete_source_by_id


async def handle_delete_source_confirm(
    client: Client, callback_query: CallbackQuery, state=None
):
    data = callback_query.data
    source_id = int(data.split("_")[-1])

    buttons = [
        [
            InlineKeyboardButton(
                "✅ Yes", callback_data=f"admin_delete_yes_{source_id}"
            ),
            InlineKeyboardButton("❌ No", callback_data="admin_delete_source_page_1"),
        ]
    ]

    markup = InlineKeyboardMarkup(buttons)

    await callback_query.message.edit_text(
        "⚠️ Yakin ingin menghapus source ini?\n\nPilih Yes atau No.",
        reply_markup=markup,
        parse_mode=ParseMode.HTML,
    )


async def handle_delete_source_yes(
    client: Client, callback_query: CallbackQuery, state=None
):
    data = callback_query.data
    source_id = int(data.split("_")[-1])

    try:
        delete_source_by_id(source_id)
        await callback_query.message.edit_text(
            "✅ Source berhasil dihapus!",
            parse_mode=ParseMode.HTML,
        )
    except Exception as e:
        await callback_query.message.edit_text(
            f"❌ Gagal menghapus source: {e}",
            parse_mode=ParseMode.HTML,
        )
