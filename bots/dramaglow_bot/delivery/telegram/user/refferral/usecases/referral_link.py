# ============================================
# referral_link.py (FINAL – MENU / EDIT)
# ============================================

from pyrogram.enums import ParseMode
from pyrogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from configs.logging_setup import log
from db.connect import get_db_cursor
from common.utils_new.menu_utils import edit_menu

BOT_USERNAME = "dramaglow_bot"
COMMISSION_RATE = 20
MIN_WITHDRAW = 50_000


def rupiah(x: int) -> str:
    return f"{x:,.0f}".replace(",", ".")


async def show_referral_link_menu(*, event: CallbackQuery):
    """
    REFERRAL LINK MENU
    - MENU (bukan ACTION)
    - EDIT jika dipanggil dari callback
    - BOOTSTRAP reply jika pertama kali
    """

    cq = event
    user = cq.from_user
    if not user:
        return

    user_id = user.id
    log.info("[REFERRAL_LINK][MENU] open user_id=%s", user_id)

    await cq.answer()

    try:
        with get_db_cursor() as (cursor, _):
            cursor.execute(
                """
                SELECT
                    affiliate_code,
                    abuse_flag,
                    referral_count,
                    affiliate_total_earned
                FROM users
                WHERE user_id = %s
                LIMIT 1
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

        affiliate_code, abuse_flag, referral_count, total_earned = row

        if not affiliate_code:
            return await edit_menu(
                event=cq,
                text=(
                    "❗ <b>Affiliate code belum tersedia.</b>\n"
                    "Silakan kirim /start ulang atau hubungi admin."
                ),
                parse_mode=ParseMode.HTML,
            )

        if abuse_flag:
            return await edit_menu(
                event=cq,
                text=(
                    "🚫 <b>Akun kamu diblokir dari sistem affiliate.</b>\n"
                    "Komisi ditahan sementara hingga diverifikasi admin."
                ),
                parse_mode=ParseMode.HTML,
            )

        referral_link = f"https://t.me/{BOT_USERNAME}?start=ref_{affiliate_code}"
        withdraw_status = (
            "TERSEDIA ✅" if total_earned >= MIN_WITHDRAW else "BELUM CUKUP ❌"
        )

        text = (
            "🎯 <b>PROGRAM AFFILIATE VIP</b>\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            f"Dapatkan <b>{COMMISSION_RATE}% komisi</b> dari setiap pembelian VIP.\n\n"
            "📊 <b>Statistik Kamu</b>\n"
            f"👥 Referral: <b>{referral_count}</b>\n"
            f"💰 Total Komisi: <b>Rp {rupiah(total_earned)}</b>\n"
            f"💸 Withdraw: <b>{withdraw_status}</b>\n\n"
            "🏦 <b>Minimal Withdraw</b>\n"
            f"Rp {rupiah(MIN_WITHDRAW)}\n\n"
            "🔗 <b>LINK REFERRAL KAMU</b>\n"
            f"<code>{referral_link}</code>\n\n"
            "📋 Salin dan bagikan link ini ke teman.\n"
            "⚠️ <i>Fraud / self-referral akan diblokir otomatis.</i>"
        )

        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "📤 Bagikan Link",
                        url=f"https://t.me/share/url?url={referral_link}",
                    ),
                ],
                [
                    InlineKeyboardButton(
                        "📊 Referral Stats", callback_data="ref_stats"
                    ),
                    InlineKeyboardButton("💵 Withdraw", callback_data="ref_withdraw"),
                ],
                [
                    InlineKeyboardButton("⬅️ Kembali ke Menu", callback_data="ref_menu"),
                ],
            ]
        )

        await edit_menu(
            event=cq,
            text=text,
            markup=keyboard,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
        )

    except Exception:
        log.exception("[REFERRAL_LINK][MENU] fatal error user_id=%s", user_id)
        await edit_menu(
            event=cq,
            text=(
                "❌ <b>Terjadi kesalahan sistem.</b>\n"
                "Silakan coba beberapa saat lagi."
            ),
            parse_mode=ParseMode.HTML,
        )
