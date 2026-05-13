import asyncio
import html

from pyrogram import Client, filters
from pyrogram.enums import ParseMode
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from configs.logging_setup import log

# Waktu sebelum pesan welcome dihapus otomatis (detik)
WELCOME_DELETE_DELAY = 300  # 5 menit


def register_welcome_handler(app: Client):
    @app.on_message(filters.new_chat_members)
    async def welcome_new_member(client: Client, message: Message):
        try:
            chat_id = message.chat.id
            new_users = message.new_chat_members or []

            # Hapus pesan join default dari Telegram
            try:
                await message.delete()
            except Exception as e:
                log.warning(f"[WELCOME] Gagal hapus pesan join default: {e}")

            # Log siapa saja yang join
            joined_info = ", ".join(f"{u.id}-{repr(u.first_name)}" for u in new_users)
            # log.info(f"📥 New members di chat {chat_id}: {joined_info}")

            # Batasi mention agar tidak spam (maksimal 5)
            limit = 5
            display_users = new_users[:limit]
            extra_count = len(new_users) - limit if len(new_users) > limit else 0

            # Buat daftar mention yang aman (escape HTML dan hapus newline)
            mentions_list = []
            for user in display_users:
                safe_name = html.escape((user.first_name or "User")).replace("\n", " ")
                mentions_list.append(
                    f"<a href='tg://user?id={user.id}'>{safe_name}</a>"
                )

            mentions = ", ".join(mentions_list)
            if extra_count > 0:
                mentions += f" dan {extra_count} lainnya"

            # Tombol inline untuk memudahkan pengguna
            keyboard = InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "🔍 Cari Drama", switch_inline_query_current_chat=""
                        )
                    ]
                ]
            )

            # Kirim pesan sambutan
            welcome_text = (
                f"👋 Selamat datang, {mentions}!\n\n"
                "Klik tombol di bawah untuk mencari drama favoritmu ⬇️"
            )

            sent_msg = await client.send_message(
                chat_id,
                welcome_text,
                reply_markup=keyboard,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True,
            )

            # Hapus otomatis setelah beberapa menit (jika diaktifkan)
            if WELCOME_DELETE_DELAY > 0:
                await asyncio.sleep(WELCOME_DELETE_DELAY)
                try:
                    await sent_msg.delete()
                except Exception as e:
                    log.warning(f"[WELCOME] Gagal hapus pesan welcome: {e}")

        except Exception as e:
            log.error(f"❌ Error di welcome_new_member handler: {e}", exc_info=True)
