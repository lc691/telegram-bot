import re

from pyrogram import Client
from pyrogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from shared.utils.escape_markdown import slugify
from configs.logging_setup import log
from database.connection import get_dict_cursor

PAGE_SIZE = 5


async def show_film_selector(
    client: Client, callback_query: CallbackQuery, page: int = 1
):
    try:
        offset = (page - 1) * PAGE_SIZE

        with get_dict_cursor() as (cursor, _):
            # Ambil daftar judul show
            cursor.execute(
                """
                SELECT DISTINCT s.title
                FROM video_stats v
                JOIN files f ON f.file_id = v.file_id
                JOIN shows s ON f.show_id = s.id
                ORDER BY s.title ASC
                OFFSET %s LIMIT %s
                """,
                (offset, PAGE_SIZE),
            )
            shows = cursor.fetchall()

            # Hitung total show untuk pagination
            cursor.execute(
                """
                SELECT COUNT(DISTINCT s.title) as total
                FROM video_stats v
                JOIN files f ON f.file_id = v.file_id
                JOIN shows s ON f.show_id = s.id
                """
            )
            total_shows = cursor.fetchone()["total"]

        if not shows:
            await callback_query.message.edit_text("📂 Tidak ada show yang ditonton.")
            return

        keyboard = []
        show_titles = [show["title"] or "Tanpa Judul" for show in shows]

        # Ambil semua link share dalam 1 query
        with get_dict_cursor() as (cursor, _):
            cursor.execute(
                """
                SELECT s.title, f.message_id, f.channel_username
                FROM files f
                JOIN shows s ON f.show_id = s.id
                WHERE s.title = ANY(%s)
                AND f.message_id IS NOT NULL
                AND f.channel_username IS NOT NULL
                ORDER BY f.date_added DESC
                """,
                (show_titles,),
            )
            link_map = {}
            for row in cursor.fetchall():
                title = row["title"]
                if title not in link_map:
                    link_map[title] = (
                        f"https://t.me/{row['channel_username']}/{row['message_id']}"
                    )

        for title in show_titles:
            slug = slugify(title) or re.sub(r"\s+", "-", title.lower())
            buttons = [
                InlineKeyboardButton(title, callback_data=f"stat_detail|{slug}|{page}")
            ]
            if title in link_map:
                buttons.append(InlineKeyboardButton("🔗 Share", url=link_map[title]))
            keyboard.append(buttons)

        # Tombol navigasi halaman
        nav_buttons = []
        if page > 1:
            nav_buttons.append(
                InlineKeyboardButton(
                    "⬅️ Prev", callback_data=f"show_film_selector|{page - 1}"
                )
            )
        if offset + PAGE_SIZE < total_shows:
            nav_buttons.append(
                InlineKeyboardButton(
                    "➡️ Next", callback_data=f"show_film_selector|{page + 1}"
                )
            )
        if nav_buttons:
            keyboard.append(nav_buttons)

        keyboard.append([InlineKeyboardButton("⬅️ Kembali", callback_data="show_stats")])

        total_pages = ((total_shows - 1) // PAGE_SIZE) + 1
        text = (
            f"🎬 Halaman {page} dari {total_pages}\n"
            "Pilih judul show untuk melihat statistik detail per episode:"
        )

        try:
            await callback_query.message.edit_text(
                text,
                reply_markup=InlineKeyboardMarkup(keyboard),
            )
        except Exception as e_edit:
            log.warning(f"[show_film_selector] Fallback ke send_message: {e_edit}")
            await client.send_message(
                chat_id=callback_query.from_user.id,
                text=text,
                reply_markup=InlineKeyboardMarkup(keyboard),
            )

    except Exception as e:
        log.error(
            f"[show_film_selector] Gagal tampilkan daftar show: {e}", exc_info=True
        )
