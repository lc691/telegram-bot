# ============================================
# referral_leaderboard_menu.py
# ============================================

from pyrogram.enums import ParseMode
from pyrogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from configs.logging_setup import log
from shared.utils.menu_utils import edit_menu
from database.connection import get_db_cursor


def rupiah(x):
    return f"{x:,.0f}".replace(",", ".")


async def show_referral_leaderboard(event: Message | CallbackQuery):
    """
    REFERRAL LEADERBOARD MENU
    - single-message UI
    - EDIT ONLY (bootstrap-aware)
    """

    user = event.from_user
    if not user:
        return

    user_id = user.id
    log.info("[REFERRAL][LEADERBOARD] open user_id=%s", user_id)

    try:
        with get_db_cursor() as (cursor, _):
            cursor.execute(
                """
                SELECT
                    a.user_id,
                    COALESCE(a.username, a.first_name, 'User') AS name,
                    SUM(acl.commission) AS total_comm,
                    COUNT(DISTINCT acl.referred_user_id) AS total_referrals,
                    MAX(acl.created_at) AS last_tx
                FROM affiliate_commission_logs acl
                JOIN users a
                    ON acl.referrer_user_id = a.user_id
                GROUP BY a.user_id, name
                HAVING SUM(acl.commission) > 0
                ORDER BY total_comm DESC
                LIMIT 10
            """
            )
            rows = cursor.fetchall()

        if not rows:
            text = "<i>Leaderboard referral masih kosong.</i>"
        else:
            text = "🏆 <b>Referral Leaderboard Top 10</b>\n"
            text += "━━━━━━━━━━━━━━━━━━━━\n\n"

            for idx, r in enumerate(rows, 1):
                last_tx = r[4].strftime("%d %b %Y") if r[4] else "-"
                text += (
                    f"{idx}. <b>{r[1]}</b>\n"
                    f"   ▸ Total Komisi: Rp {rupiah(r[2])}\n"
                    f"   ▸ Referral Valid: {r[3]}\n"
                    f"   ▸ Transaksi Terakhir: {last_tx}\n\n"
                )

        keyboard = InlineKeyboardMarkup(
            [[InlineKeyboardButton("⬅️ Kembali", callback_data="ref_menu")]]
        )

        await edit_menu(
            event=event,
            text=text,
            markup=keyboard,
            parse_mode=ParseMode.HTML,
        )

    except Exception:
        log.exception("[REFERRAL][LEADERBOARD] fatal user_id=%s", user_id)
        await edit_menu(
            event=event,
            text="❌ Terjadi kesalahan sistem.",
        )
