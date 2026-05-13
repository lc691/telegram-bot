from html import escape

from pyrogram import Client
from pyrogram.enums import ParseMode
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from bots.dramaglow_bot.repository.search_repository import log_search_query
from common.utils.escape_markdown import slugify
from common.utils.search_state_manager import UserSearchStateManager
from configs.logging_setup import log
from db.connect import get_dict_cursor


async def handle_search_text(client: Client, message: Message) -> bool:
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name or "Unknown"
    fsm = UserSearchStateManager(user_id)

    # Cek apakah user memang sedang dalam mode pencarian
    if fsm.get_step() != "awaiting_input":
        return False

    raw_title = (message.text or "").strip()
    title = " ".join(raw_title.split()).title()

    if not title:
        await message.reply("⚠️ Judul tidak boleh kosong. Coba ketik ulang.")
        return True

    log.info(f"[Search] Pencarian '{title}' oleh user_id={user_id}")

    try:
        # 1️⃣ Coba cari judul yang cocok persis
        with get_dict_cursor() as (cursor, _):
            cursor.execute(
                """
                SELECT id, title, thumbnail
                FROM shows
                WHERE LOWER(title) = %s
                LIMIT 1
                """,
                (title.lower(),),
            )
            show_row = cursor.fetchone()

        if show_row:
            show_id = show_row["id"]
            show_title = show_row["title"]
            thumbnail = show_row["thumbnail"] or "https://example.com/default-thumb.jpg"

            # Ambil satu file saja untuk dapatkan message_id
            with get_dict_cursor() as (cursor, _):
                cursor.execute(
                    "SELECT message_id FROM files WHERE show_id = %s LIMIT 1",
                    (show_id,),
                )
                file_row = cursor.fetchone()

            log_search_query(user_id, username, title, matched=True)

            if file_row:
                post_link = f"https://t.me/dramaglow/{file_row['message_id']}"
                caption = (
                    f"🎬 <b>{escape(show_title)}</b>\n"
                    f"📺 <a href='{post_link}'>Tonton Sekarang</a>"
                )
            else:
                caption = f"🎬 <b>{escape(show_title)}</b>\n❌ Belum ada file tersedia."

            await message.reply_photo(
                photo=thumbnail,
                caption=caption,
                parse_mode=ParseMode.HTML,
            )
            fsm.clear_all()
            return True

        # 2️⃣ Jika tidak ditemukan, cari yang mirip
        log_search_query(user_id, username, title, matched=False)

        with get_dict_cursor() as (cursor, _):
            cursor.execute(
                """
                SELECT id, title
                FROM shows
                WHERE title ILIKE %s
                ORDER BY title
                LIMIT 20
                """,
                (f"%{title}%",),
            )
            similar_rows = cursor.fetchall()

        if similar_rows:
            # 🔹 Simpan hasil mirip ke state
            fsm.set_data(
                "search_results",
                [
                    {"title": row["title"], "slug": slugify(row["title"])[:50]}
                    for row in similar_rows
                ],
            )

            buttons = [
                [
                    InlineKeyboardButton(
                        text=escape(row["title"]),
                        callback_data=f"show_detail|{slugify(row['title'])[:50]}",
                    )
                ]
                for row in similar_rows
            ]

            # Tambahkan tombol request & kembali
            buttons += [
                [
                    InlineKeyboardButton(
                        "📥 Request Judul Ini", callback_data=f"request_film|{title}"
                    )
                ],
                [InlineKeyboardButton("⬅️ Kembali", callback_data="back_to_search")],
            ]

            await message.reply(
                f"🔍 Judul <b>{escape(title)}</b> tidak ditemukan persis.\n"
                f"Berikut beberapa yang mirip:",
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup(buttons),
            )

            # ⛔ Jangan hapus state, karena akan dipakai saat "⬅️ Kembali"
            fsm.set_step(None)
            return True

        # 3️⃣ Tidak ada hasil sama sekali
        await message.reply(
            f"❌ Tidak ditemukan judul yang mirip dengan: <b>{escape(title)}</b>",
            parse_mode=ParseMode.HTML,
        )
        fsm.clear_all()
        return True

    except Exception as e:
        log.exception(f"[handle_search_text] Error user_id={user_id}: {e}")
        await message.reply("❌ Gagal melakukan pencarian. Silakan coba lagi nanti.")
        fsm.clear_all()
        return True
