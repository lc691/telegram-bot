from pyrogram import Client, filters
from pyrogram.enums import ChatType, ParseMode
from pyrogram.handlers import CallbackQueryHandler, MessageHandler

from .callbacks import referral_callback_handler
from ..menu import show_referral_menu


# =====================================================
# ENTRYPOINT (GROUP REDIRECT → PRIVATE)
# =====================================================
async def referral_menu_entrypoint(client: Client, message):

    # Jika di grup → redirect ke private
    if message.chat.type in (ChatType.GROUP, ChatType.SUPERGROUP):

        try:
            await message.reply(
                "⚠️ <b>Menu Referral hanya bisa dibuka di Private Chat.</b>\n\n"
                "👉 <a href='https://t.me/drac1n_bot?start=referral'>Klik di sini untuk membuka</a>",
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True,
            )
        except Exception:
            await message.reply(
                "❗ Tidak bisa mengarahkan ke private.\n"
                "Silakan buka bot dan kirim: /referral",
                parse_mode=ParseMode.HTML,
            )
        return

    # Jika private → tampilkan menu
    await show_referral_menu(
        event=message,
    )


# =====================================================
# REGISTER HANDLER
# =====================================================
def register_referral(app):

    app.add_handler(
        MessageHandler(
            referral_menu_entrypoint,
            filters.command(["referral", "r_menu", "r_link"]),
        ),
        group=1,
    )

    app.add_handler(
        CallbackQueryHandler(
            referral_callback_handler,
            filters.regex(r"^ref_"),
        ),
        group=1,
    )
