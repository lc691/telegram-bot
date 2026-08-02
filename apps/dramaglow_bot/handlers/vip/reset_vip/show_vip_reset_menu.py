# bots/dramaglow_bot/handlers/vip/reset_vip/show_vip_reset_menu.py

from pyrogram.enums import ParseMode
from pyrogram.types import CallbackQuery

from apps.dramaglow_bot.keyboard.vip_tools import generate_vip_reset_menu
from configs.logging_setup import log


async def show_vip_reset_menu(client, callback_query: CallbackQuery):
    try:
        await callback_query.message.edit_text(
            "♻️ Pilih jenis reset VIP:",
            reply_markup=generate_vip_reset_menu(),
            parse_mode=ParseMode.HTML,
        )
    except Exception as e:
        log.error(f"[VIP_RESET_MENU] Gagal tampilkan menu reset: {e}", exc_info=True)
        await callback_query.answer("❌ Gagal tampilkan menu reset.", show_alert=True)
