from html import escape

from pyrogram import Client
from pyrogram.enums import ParseMode
from pyrogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputMediaPhoto,
)

from configs.logging_setup import log
from db.connect import get_dict_cursor

from ...repository.posting.post_show_utils import resolve_thumbnail


async def show_film_detail(client: Client, callback_query: CallbackQuery, slug: str):
    try:
        # Pisahkan slug dan halaman (format: stat_detail|slug|page)
        parts = slug.split("|")
        slug = parts[0]
        page = parts[1] if len(parts) > 1 else "1"

        with get_dict_cursor() as (cursor, _):
            cursor.execute(
                """
                SELECT DISTINCT f.main_title, s.title AS show_title,
                       s.genre, s.sinopsis, s.thumbnail
                FROM files f
                LEFT JOIN shows s ON f.show_id = s.id
                WHERE LOWER(REGEXP_REPLACE(f.main_title, '[^a-zA-Z0-9]+', '-', 'g')) = %s
                LIMIT 1
                """,
                (slug,),
            )
            row = cursor.fetchone()

        if not row:
            await callback_query.message.edit_text("❌ Judul tidak ditemukan.")
            return

        main_title = row["main_title"]
        show_title = row["show_title"] or "Tanpa Judul"
        genre = row["genre"] or "-"
        sinopsis = row["sinopsis"] or "-"
        thumbnail = row["thumbnail"]

        # Ambil semua episode dan view
        with get_dict_cursor() as (cursor, _):
            cursor.execute(
                """
                SELECT f.file_name, SUM(v.play_count) AS total_views
                FROM files f
                JOIN video_stats v ON v.file_id = f.file_id
                WHERE f.main_title = %s
                GROUP BY f.file_name
                ORDER BY f.file_name
                """,
                (main_title,),
            )
            episodes = cursor.fetchall()

        if not episodes:
            await callback_query.message.edit_text(
                "❌ Belum ada penayangan untuk judul ini."
            )
            return

        # Ambil link untuk dibagikan (optional)
        with get_dict_cursor() as (cursor, _):
            cursor.execute(
                """
                SELECT message_id, channel_username
                FROM files
                WHERE main_title = %s
                AND message_id IS NOT NULL AND channel_username IS NOT NULL
                ORDER BY date_added DESC
                LIMIT 1
                """,
                (main_title,),
            )
            link_row = cursor.fetchone()

        # Susun caption
        text = f"<b>{escape(show_title)}</b>\n"
        text += f"Genre: {genre}\n"
        text += "━━━━━━━━━━━━━━━━━━━\n"
        text += f"<pre>💨 Sinopsis\n{escape(sinopsis)}</pre>\n\n"
        text += "━━━━━━━━━━━━━━━━━━━\n"
        text += f"📊 <b>Statistik Penayangan:</b>\n"

        for i, ep in enumerate(episodes, 1):
            views = ep["total_views"] or 0
            file_name = ep["file_name"]
            text += f"{i}. {file_name} — 👁️ {views}x\n"

        if link_row:
            share_url = (
                f"https://t.me/{link_row['channel_username']}/{link_row['message_id']}"
            )
            text += "━━━━━━━━━━━━━━━━━━━\n"
            text += f"📎 <b>Link:</b> <code>{share_url}</code>"

        # Tombol kembali
        keyboard = [
            [
                InlineKeyboardButton(
                    "⬅️ Kembali", callback_data=f"show_film_selector|{page}"
                )
            ]
        ]

        # Tampilkan thumbnail atau fallback ke text
        try:
            if thumbnail:
                log.debug(f"[show_film_detail] Thumbnail awal: {thumbnail}")
                resolved_thumbnail = await resolve_thumbnail(thumbnail)
                log.debug(f"[show_film_detail] Thumbnail final: {resolved_thumbnail}")

                if callback_query.message.photo or callback_query.message.video:
                    await callback_query.message.edit_media(
                        media=InputMediaPhoto(
                            media=resolved_thumbnail,
                            caption=text,
                            parse_mode=ParseMode.HTML,
                        ),
                        reply_markup=InlineKeyboardMarkup(keyboard),
                    )
                else:
                    try:
                        await callback_query.message.delete()
                    except Exception as e_del:
                        log.warning(f"[show_film_detail] Gagal hapus pesan: {e_del}")

                    await client.send_photo(
                        chat_id=callback_query.message.chat.id,
                        photo=resolved_thumbnail,
                        caption=text,
                        parse_mode=ParseMode.HTML,
                        reply_markup=InlineKeyboardMarkup(keyboard),
                    )

            else:
                raise Exception("Thumbnail kosong atau tidak valid")

        except Exception as e:
            log.warning(f"[show_film_detail] Gagal tampilkan thumbnail: {e}")
            try:
                await callback_query.message.edit_text(
                    text,
                    parse_mode=ParseMode.HTML,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                )
            except Exception as fallback_err:
                log.error(
                    f"[show_film_detail] Gagal edit_text fallback: {fallback_err}"
                )
                try:
                    await client.send_message(
                        chat_id=callback_query.from_user.id,
                        text=text,
                        parse_mode=ParseMode.HTML,
                        reply_markup=InlineKeyboardMarkup(keyboard),
                    )
                except Exception as send_msg_err:
                    log.error(
                        f"[show_film_detail] Gagal kirim fallback message: {send_msg_err}"
                    )

    except Exception as e:
        log.error(f"[show_film_detail] Gagal ambil detail '{slug}': {e}", exc_info=True)
        try:
            await callback_query.message.edit_text("❌ Gagal menampilkan detail film.")
        except:
            await client.send_message(
                chat_id=callback_query.from_user.id,
                text="❌ Gagal menampilkan detail film.",
            )
