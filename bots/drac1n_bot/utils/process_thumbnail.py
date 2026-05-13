from uuid import uuid4

from pyrogram.enums import ParseMode

from common.utils.escape_markdown import beautify_file_name
from config import DB_DRAMA
from configs.logging_setup import log
from db.connect import get_db_cursor

IMAGE_EXTENSIONS = [".jpg", ".jpeg", ".png", ".webp"]


def is_image_file(name: str, mime_type: str = "") -> bool:
    image_ext = any(name.lower().endswith(ext) for ext in IMAGE_EXTENSIONS)
    image_mime = mime_type.startswith("image/")
    return image_ext or image_mime


async def process_thumbnail_if_applicable(client, message, bot_username_cache):
    file_id = None
    file_name = None

    # Gambar dikirim sebagai dokumen
    if message.document and is_image_file(message.document.file_name or ""):
        file_id = message.document.file_id
        file_name = message.document.file_name

    # Gambar dikirim sebagai photo biasa (tanpa file name)
    elif message.photo:
        if not message.caption:
            await message.reply_text(
                "⚠️ Gambar harus diberi caption sesuai judul tayangan."
            )
            return True
        file_id = message.photo.file_id
        file_name = message.caption.strip()

    if not file_id or not file_name:
        return False

    log.info(f"[Thumbnail] Diterima gambar: '{file_name}'")

    main_title = beautify_file_name(file_name)
    log.info(f"[Thumbnail] Parsed main_title: '{main_title}'")

    try:
        if not bot_username_cache:
            bot_username_cache = (await client.get_me()).username
    except Exception as e:
        bot_username_cache = "drac1n_bot"
        log.warning(f"[Thumbnail] Fallback username: {e}")

    file_url = f"https://t.me/{bot_username_cache}?start=img_{file_id}"

    try:
        with get_db_cursor() as (cursor, conn):
            cursor.execute("SELECT id FROM shows WHERE title ILIKE %s", (main_title,))
            row = cursor.fetchone()

            if row:
                show_id = row[0]
                cursor.execute(
                    "UPDATE shows SET thumbnail = %s WHERE id = %s",
                    (file_url, show_id),
                )
                conn.commit()
                await message.reply(
                    f"✅ Thumbnail untuk <b>{main_title}</b> berhasil diupdate.",
                    parse_mode=ParseMode.HTML,
                )

                # ✅ Hapus pesan asli jika update berhasil
                try:
                    await message.delete()
                    log.info(f"[Thumbnail] Pesan berhasil dihapus untuk: {file_name}")
                except Exception as e:
                    log.warning(f"[Thumbnail] Gagal hapus pesan: {e}")

            else:
                await message.reply(
                    f"⚠️ Gagal update thumbnail: Judul <b>{main_title}</b> belum ada di database.",
                    parse_mode=ParseMode.HTML,
                )

        return True

    except Exception as e:
        log.exception(f"[Thumbnail] ❌ Gagal update thumbnail DB: {e}")
        await message.reply_text("❌ Terjadi kesalahan saat mengupdate thumbnail.")
        return True
