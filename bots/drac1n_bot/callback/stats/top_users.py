from pyrogram.enums import ParseMode
from pyrogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from configs.logging_setup import log
from db.connect import get_dict_cursor


async def show_top_users(callback_query: CallbackQuery):
    try:
        with get_dict_cursor() as (cursor, _):
            cursor.execute(
                """
                SELECT u.username, u.first_name, v.user_id, SUM(v.play_count) AS total_views
                FROM video_stats v
                JOIN users u ON u.user_id = v.user_id
                GROUP BY v.user_id, u.username, u.first_name
                ORDER BY total_views DESC
                LIMIT 10
            """
            )
            rows = cursor.fetchall()

        if not rows:
            text = "📉 Belum ada user yang menonton video."
        else:
            text = "👤 <b>Top 10 Pengguna Paling Aktif</b>\n\n"
            for i, row in enumerate(rows, 1):
                username = row["username"]
                first_name = row["first_name"] or "-"
                user_display = f"@{username}" if username else first_name
                text += f"{i}. {user_display} — 👁️ {row['total_views']}x\n"

        await callback_query.message.edit_text(
            text,
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("⬅️ Kembali", callback_data="show_stats")]]
            ),
        )

    except Exception as e:
        log.error(f"[show_top_users] Gagal ambil data user aktif: {e}", exc_info=True)
        await callback_query.message.edit_text("❌ Gagal menampilkan statistik user.")
