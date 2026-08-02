# ============================================================
# referral_stats.py (FINAL – MENU / EDIT)
# ============================================================

from pyrogram.enums import ParseMode
from pyrogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from configs.logging_setup import log
from database.connection import get_db_cursor
from shared.utils.menu_utils import edit_menu

MIN_WITHDRAW = 50_000


def rupiah(x: int) -> str:
    return f"{x:,.0f}".replace(",", ".")


async def show_referral_stats_menu(*, event: CallbackQuery):
    """
    REFERRAL STATS MENU
    - MENU (EDIT ONLY)
    - single-message UI
    """

    cq = event
    user = cq.from_user
    if not user:
        return

    user_id = user.id
    log.info("[REFERRAL_STATS][MENU] open user_id=%s", user_id)

    await cq.answer()

    try:
        # ===============================
        # 1️⃣ Affiliate summary
        # ===============================
        with get_db_cursor() as (cursor, _):
            cursor.execute(
                """
                SELECT
                    affiliate_balance,
                    affiliate_total_earned,
                    referral_count,
                    abuse_flag
                FROM users
                WHERE user_id = %s
                """,
                (user_id,),
            )
            row = cursor.fetchone()

        if not row:
            return await edit_menu(
                event=cq,
                text=(
                    "❗ <b>Akun belum terdaftar.</b>\n"
                    "Silakan kirim /start terlebih dahulu."
                ),
                parse_mode=ParseMode.HTML,
            )

        affiliate_balance, affiliate_total, referral_count, abuse_flag = row

        # ===============================
        # 2️⃣ Top referral
        # ===============================
        with get_db_cursor() as (cursor, _):
            cursor.execute(
                """
                SELECT
                    u.username,
                    u.first_name,
                    SUM(acl.commission) AS total_comm,
                    MAX(acl.created_at) AS last_tx
                FROM affiliate_commission_logs acl
                JOIN users u
                    ON u.user_id = acl.referred_user_id
                WHERE acl.referrer_user_id = %s
                GROUP BY u.user_id, u.username, u.first_name
                HAVING SUM(acl.commission) > 0
                ORDER BY total_comm DESC
                LIMIT 10
                """,
                (user_id,),
            )
            rows = cursor.fetchall()

        if rows:
            ref_list = ""
            for idx, r in enumerate(rows, 1):
                name = r[0] or r[1] or "User"
                last_tx = r[3].strftime("%d %b %Y") if r[3] else "-"
                ref_list += (
                    f"{idx}. <b>{name}</b>\n"
                    f"   ▸ Total Komisi: Rp {rupiah(r[2])}\n"
                    f"   ▸ Transaksi Terakhir: {last_tx}\n\n"
                )
        else:
            ref_list = "<i>Belum ada referral yang menghasilkan komisi.</i>\n"

        # ===============================
        # 3️⃣ Withdraw status
        # ===============================
        if abuse_flag:
            wd_status = "DIBLOKIR 🚫"
            abuse_text = (
                "\n⚠️ <b>Status Akun:</b> TERBATASI\n"
                "Komisi ditahan sementara hingga verifikasi admin.\n\n"
            )
        elif affiliate_balance >= MIN_WITHDRAW:
            wd_status = "TERSEDIA ✅"
            abuse_text = ""
        else:
            wd_status = "BELUM CUKUP ❌"
            abuse_text = ""

        text = (
            "🎯 <b>AFFILIATE DASHBOARD</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👥 Referral Valid: <b>{referral_count}</b>\n"
            f"💰 Total Komisi: <b>Rp {rupiah(affiliate_total)}</b>\n"
            f"🏦 Saldo Aktif: <b>Rp {rupiah(affiliate_balance)}</b>\n"
            f"💸 Withdraw: <b>{wd_status}</b>\n"
            f"{abuse_text}"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "<b>Top Referral</b>\n"
            f"{ref_list}"
        )

        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("🔗 Referral Link", callback_data="ref_link"),
                    InlineKeyboardButton("💵 Withdraw", callback_data="ref_withdraw"),
                ],
                [InlineKeyboardButton("⬅️ Kembali ke Menu", callback_data="ref_menu")],
            ]
        )

        await edit_menu(
            event=cq,
            text=text,
            markup=keyboard,
            parse_mode=ParseMode.HTML,
        )

    except Exception:
        log.exception("[REFERRAL_STATS][MENU] fatal user_id=%s", user_id)
        await edit_menu(
            event=cq,
            text="❌ Terjadi kesalahan sistem.",
            parse_mode=ParseMode.HTML,
        )
