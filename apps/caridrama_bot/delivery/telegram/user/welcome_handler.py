import asyncio
import html

from pyrogram import Client, filters
from pyrogram.enums import ParseMode
from pyrogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from configs.logging_setup import log

WELCOME_DELETE_DELAY = 300  # 5 menit


async def auto_delete_message(message: Message, delay: int):
    """Hapus pesan otomatis setelah delay."""
    try:
        await asyncio.sleep(delay)
        await message.delete()
    except Exception as e:
        log.warning(f"[WELCOME] Gagal hapus pesan welcome: {e}")


def build_mentions(users, limit=5):
    """Buat mention user yang aman untuk HTML."""
    display_users = users[:limit]
    extra_count = max(0, len(users) - limit)

    mentions = []

    for user in display_users:
        safe_name = html.escape(
            (user.first_name or "User").replace("\n", " ")
        )

        mentions.append(
            f"<a href='tg://user?id={user.id}'>{safe_name}</a>"
        )

    result = ", ".join(mentions)

    if extra_count:
        result += f" dan {extra_count} lainnya"

    return result


def register_welcome_handler(app: Client):

    @app.on_message(filters.new_chat_members)
    async def welcome_new_member(client: Client, message: Message):

        try:
            chat_id = message.chat.id
            new_users = message.new_chat_members or []

            if not new_users:
                return

            # Hapus pesan join bawaan Telegram
            try:
                await message.delete()
            except Exception as e:
                log.warning(
                    f"[WELCOME] Gagal hapus pesan join default: {e}"
                )

            mentions = build_mentions(new_users)

            keyboard = InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "🔍 Cari Drama",
                            switch_inline_query_current_chat=""
                        )
                    ]
                ]
            )

            welcome_text = (
                f"👋 <b>Selamat datang! {mentions}</b>\n\n"
                "📺 Sekarang kamu bisa mencari drama favorit "
                "langsung dari grup ini.\n"
                "🔎 Tekan tombol di bawah lalu ketik judul drama "
                "yang ingin kamu cari 👇"
            )

            sent_msg = await client.send_message(
                chat_id=chat_id,
                text=welcome_text,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard,
                disable_web_page_preview=True,
            )

            # Auto delete tanpa blocking handler
            if WELCOME_DELETE_DELAY > 0:
                asyncio.create_task(
                    auto_delete_message(
                        sent_msg,
                        WELCOME_DELETE_DELAY
                    )
                )

        except Exception as e:
            log.error(
                f"❌ Error di welcome_new_member handler: {e}",
                exc_info=True
            )