from pyrogram.enums import ParseMode
from pyrogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    CallbackQuery,
)

from configs.logging_setup import log
from shared.utils.menu_utils import edit_menu
from .audit import audit_log


async def show_referral_menu(event: Message | CallbackQuery):
    """
    REFERRAL MENU
    - single-message UI
    - EDIT ONLY (bootstrap-aware)
    """

    user = event.from_user
    if not user:
        return

    user_id = user.id
    audit_log("OPEN_MENU", user_id)

    text = (
        "🎯 <b>PROGRAM AFFILIATE VIP DCSTV</b>\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        "💰 <b>Dapatkan KOMISI hingga 20% dari setiap pembelian VIP!</b>\n\n"
        "Ajak teman kamu untuk bergabung menggunakan link referral milikmu.\n"
        "Setiap mereka membeli VIP, kamu langsung mendapat komisi otomatis.\n\n"
        "🚀 <b>Keuntungan Join Affiliate:</b>\n"
        "✅ Komisi besar tanpa batas\n"
        "✅ Tanpa modal, 100% gratis\n"
        "✅ Bisa dicairkan ke OVO, DANA, GOPAY, dan BANK\n"
        "✅ Statistik real-time & transparan\n\n"
        "🛡️ <b>Aman & Terpercaya</b>\n"
        "Sistem otomatis melacak semua referral kamu.\n"
        "Anti fraud & self-referral.\n\n"
        "👇 <b>Pilih menu di bawah untuk mulai menghasilkan:</b>"
    )

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "💰 Cari CUAN 🔥 Komisi 20%",
                    url="https://t.me/+Kc253522ioY4MDA1",
                )
            ],
            [
                InlineKeyboardButton("🔗 Referral Link", callback_data="ref_link"),
                InlineKeyboardButton("💵 Withdraw", callback_data="ref_withdraw"),
            ],
            [
                InlineKeyboardButton("🏆 Leaderboard", callback_data="ref_leaderboard"),
                InlineKeyboardButton("🚪 Close", callback_data="close"),
            ],
        ]
    )

    try:
        await edit_menu(
            event=event,
            text=text,
            markup=keyboard,
            parse_mode=ParseMode.HTML,
        )

        log.info("[REFERRAL][MENU] rendered user_id=%s", user_id)

    except Exception:
        log.exception("[REFERRAL][MENU] render failed user_id=%s", user_id)
        await edit_menu(
            event=event,
            text="⚠️ Gagal memuat menu referral.\nSilakan coba lagi.",
        )
