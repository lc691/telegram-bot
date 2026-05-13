from pyrogram.enums import ParseMode
from pyrogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from configs.logging_setup import log
from common.utils_new.menu_utils import edit_menu
from .audit import audit_log


async def show_withdraw_menu(*, event: CallbackQuery):
    """
    WITHDRAW INSTRUCTIONS MENU
    - MENU (EDIT)
    - single-message UI
    - READ ONLY
    """
    cq = event
    user = cq.from_user
    if not user:
        return

    user_id = user.id
    audit_log("OPEN_WITHDRAW", user_id)
    log.info("[REFERRAL_WITHDRAW][MENU] open user_id=%s", user_id)

    await cq.answer()

    text = (
        "💵 <b>WITHDRAW AFFILIATE</b>\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        "Gunakan format berikut:\n"
        "<code>/r_wd &lt;metode&gt; &lt;jumlah&gt; &lt;tujuan&gt;</code>\n\n"
        "Contoh:\n"
        "<code>/r_wd ovo 100000 081234567890</code>\n\n"
        "Metode tersedia:\n"
        "• OVO\n"
        "• DANA\n"
        "• GOPAY\n"
        "• BANK"
    )

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "⬅️ Kembali ke Menu",
                    callback_data="ref_menu",
                )
            ]
        ]
    )

    await edit_menu(
        event=cq,
        text=text,
        markup=keyboard,
        parse_mode=ParseMode.HTML,
    )
