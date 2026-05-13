from pyrogram.enums import ParseMode
from pyrogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from configs.logging_setup import log
from db.connect import get_dict_cursor


async def show_vip_vs_free(callback_query: CallbackQuery):
    try:
        with get_dict_cursor() as (cursor, _):
            cursor.execute(
                """
                SELECT u.is_vip, SUM(v.play_count) AS total_views
                FROM video_stats v
                JOIN users u ON u.user_id = v.user_id
                GROUP BY u.is_vip
            """
            )
            rows = cursor.fetchall()

        total_vip = 0
        total_free = 0

        for row in rows:
            if row["is_vip"]:
                total_vip = row["total_views"]
            else:
                total_free = row["total_views"]

        total_all = total_vip + total_free
        vip_pct = round((total_vip / total_all) * 100, 1) if total_all > 0 else 0
        free_pct = 100 - vip_pct

        text = (
            "💎 <b>Statistik View: VIP vs Gratis</b>\n\n"
            f"👤 Non-VIP: {total_free}x ({free_pct}%)\n"
            f"👑 VIP: {total_vip}x ({vip_pct}%)\n\n"
            f"📊 Total View: {total_all}x"
        )

        await callback_query.message.edit_text(
            text,
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("⬅️ Kembali", callback_data="show_stats")]]
            ),
        )

    except Exception as e:
        log.error(f"[show_vip_vs_free] Gagal ambil statistik VIP: {e}", exc_info=True)
        await callback_query.message.edit_text(
            "❌ Gagal menampilkan statistik VIP vs Gratis."
        )
