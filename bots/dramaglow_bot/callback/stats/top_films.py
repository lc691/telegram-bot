from pyrogram.enums import ParseMode
from pyrogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from configs.logging_setup import log
from db.connect import get_dict_cursor


async def show_top_films(callback_query: CallbackQuery):
    try:
        with get_dict_cursor() as (cursor, _):
            cursor.execute(
                """
                SELECT f.main_title, SUM(v.play_count) AS total_views
                FROM video_stats v
                JOIN files f ON v.file_id = f.file_id
                GROUP BY f.main_title
                ORDER BY total_views DESC
                LIMIT 10
            """
            )
            rows = cursor.fetchall()

        if not rows:
            text = "📉 Belum ada data film yang ditonton."
        else:
            text = "📊 <b>Top 10 Film Paling Banyak Ditonton</b>\n\n"
            for i, row in enumerate(rows, 1):
                text += f"{i}. {row['main_title']} — 👁️ {row['total_views']}x\n"

        await callback_query.message.edit_text(
            text,
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("⬅️ Kembali", callback_data="show_stats")]]
            ),
        )

    except Exception as e:
        log.error(f"[show_top_films] Gagal ambil statistik: {e}", exc_info=True)
        await callback_query.message.edit_text("❌ Gagal menampilkan statistik film.")
