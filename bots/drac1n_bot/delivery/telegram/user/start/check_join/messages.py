# # modules/messages.py
# from pyrogram.enums import ParseMode
# from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

# from configs.logging_setup import log

# from ..services.greeting import get_country_code_by_language, get_greeting_by_country


# async def send_join_instructions(app, message, not_joined, access_hash):
#     """Kirim pesan berisi instruksi join channel."""
#     try:
#         language_code = getattr(message.from_user, "language_code", "id")
#         country_code = get_country_code_by_language(language_code)
#         greeting = get_greeting_by_country(country_code)

#         if not getattr(app.me, "username", None):
#             await app.get_me()

#         restart_link = f"https://t.me/{app.me.username}?start={access_hash}"
#         join_links = "\n".join(
#             f"👉 <a href='{url}'>@{username}</a>" for username, url in not_joined
#         )

#         user_name = message.from_user.first_name or "User"
#         message_text = (
#             f"👋 {greeting}, <b>{user_name}</b>!\n\n"
#             "🚫 <b>Kamu belum bisa menonton saat ini.</b>\n\n"
#             "Sebelum melanjutkan, pastikan kamu sudah <b>BERGABUNG</b> ke semua channel berikut:\n\n"
#             f"{join_links}\n\n"
#             "✅ Setelah bergabung, klik tombol di bawah ini untuk melanjutkan.\n\n"
#             "❓ Ada pertanyaan? Hubungi admin: <a href='https://t.me/mimindcstv'>@mimindcstv</a>"
#         )

#         await message.reply_text(
#             message_text,
#             reply_markup=InlineKeyboardMarkup(
#                 [[InlineKeyboardButton("🔁 Saya sudah bergabung", url=restart_link)]]
#             ),
#             parse_mode=ParseMode.HTML,
#             disable_web_page_preview=True,
#         )
#         log.info(f"📨 Instruksi join dikirim ke {message.from_user.id}")

#     except Exception as e:
#         log.exception(f"❌ Gagal kirim pesan join ke {message.from_user.id}: {e}")


# modules/messages.py
from pyrogram.enums import ParseMode
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from configs.logging_setup import log

from ..services.greeting import get_country_code_by_language, get_greeting_by_country


from html import escape


async def send_join_instructions(app, message, not_joined, access_hash):
    """
    Send join instruction message safely.
    """

    try:
        user = message.from_user
        if not user:
            log.warning("[JOIN_MSG] message without from_user")
            return

        language_code = getattr(user, "language_code", "id") or "id"
        country_code = get_country_code_by_language(language_code)
        greeting = get_greeting_by_country(country_code)

        # Ensure bot username loaded
        if not getattr(app.me, "username", None):
            await app.get_me()

        bot_username = app.me.username
        if not bot_username:
            log.error("[JOIN_MSG] bot username missing")
            return

        if not access_hash:
            access_hash = "start"

        restart_link = f"https://t.me/{bot_username}?start={access_hash}"

        join_links = "\n".join(
            f"👉 <a href='{escape(url)}'>@{escape(username)}</a>"
            for username, url in not_joined
        )

        user_name = escape(user.first_name or "User")

        message_text = (
            f"👋 {greeting}, <b>{user_name}</b>!\n\n"
            "🚫 <b>Kamu belum bisa menonton saat ini.</b>\n\n"
            "Sebelum melanjutkan, pastikan kamu sudah <b>BERGABUNG</b> ke semua channel berikut:\n\n"
            f"{join_links}\n\n"
            "✅ Setelah bergabung, klik tombol di bawah ini untuk melanjutkan.\n\n"
            "❓ Ada pertanyaan? Hubungi admin: "
            "<a href='https://t.me/mimindcstv'>@mimindcstv</a>"
        )

        await message.reply_text(
            message_text,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("🔁 Saya sudah bergabung", url=restart_link)]]
            ),
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
        )

        log.info("[JOIN_MSG] sent to user_id=%s", user.id)

    except Exception:
        log.exception(
            "[JOIN_MSG] failed sending to user_id=%s",
            getattr(message.from_user, "id", None),
        )
