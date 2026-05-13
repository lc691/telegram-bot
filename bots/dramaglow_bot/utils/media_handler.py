import os

from datetime import datetime, timezone

from pyrogram import Client
from pyrogram.enums import ParseMode
from pyrogram.types import Message

from common.utils.callback_helpers import safe_reply
from common.utils.escape_markdown import format_size
from configs.logging_setup import log
from db.connect import get_db_cursor, get_dict_cursor


async def send_file_by_id(message, file_db_id, user_id, vip=False, reply_markup=None):
    log.info(
        f"[SEND FILE BY ID] ▶ Mulai proses kirim file | file_db_id={file_db_id} | user_id={user_id} | VIP={vip}"
    )

    try:
        with get_dict_cursor() as (cursor, _):
            row = None

            # Step 1: Deteksi apakah file_db_id adalah file_id Telegram
            if not str(file_db_id).isdigit():
                log.debug(
                    f"[SEND FILE BY ID] 🔍 Deteksi file_id Telegram: {file_db_id}"
                )
                cursor.execute(
                    "SELECT id, file_id, file_type, file_name FROM files WHERE file_id = %s",
                    (file_db_id,),
                )
                row = cursor.fetchone()
                if not row:
                    log.warning(
                        f"[SEND FILE BY ID] ⚠️ File_id {file_db_id} tidak ditemukan di DB"
                    )
                    await message.reply_text(
                        "⚠️ File tidak ditemukan di database.",
                        parse_mode=ParseMode.HTML,
                    )
                    return
                file_db_id = row["id"]

            # Step 2: Jika belum ada data row, ambil berdasarkan ID DB
            if not row:
                log.debug(
                    f"[SEND FILE BY ID] 🔍 Ambil data file berdasarkan ID: {file_db_id}"
                )
                cursor.execute(
                    "SELECT id, file_id, file_type, file_name FROM files WHERE id = %s",
                    (int(file_db_id),),
                )
                row = cursor.fetchone()
                if not row:
                    log.warning(
                        f"[SEND FILE BY ID] ⚠️ file_db_id {file_db_id} tidak ditemukan di DB"
                    )
                    await message.reply_text(
                        "⚠️ File tidak ditemukan di database.",
                        parse_mode=ParseMode.HTML,
                    )
                    return

        # Step 3: Kirim file
        await send_file_by_type(
            message=message,
            file_type=row["file_type"],
            file_id=row["file_id"],
            name=row["file_name"],
            user_id=user_id,
            vip=vip,
            reply_markup=reply_markup,
        )

        log.info(
            f"[SEND FILE BY ID] ✅ Selesai kirim file | ID={file_db_id} | Type={row['file_type']} | User={user_id} | VIP={vip}"
        )

    except Exception as e:
        log.error(
            f"[SEND FILE BY ID] ❌ Gagal kirim file | ID={file_db_id} | User={user_id} | Error={e}",
            exc_info=True,
        )
        await message.reply_text(
            "❗ Terjadi kesalahan saat mengirim file. Silakan coba lagi nanti.",
            parse_mode=ParseMode.HTML,
        )


async def send_file_by_type(
    message, file_type, file_id, name, user_id, vip=False, reply_markup=None
):
    log.info(
        f"[SEND FILE] ▶ Mulai kirim file | Type={file_type} | Name='{name}' | User={user_id} | VIP={vip}"
    )

    try:
        now = datetime.now(timezone.utc)
        client = getattr(message, "_client", None)

        if not client:
            log.error("[SEND FILE] ❌ _client tidak tersedia di message object")
            await message.reply_text("❌ Internal error: client tidak tersedia.")
            return

        name_without_ext = os.path.splitext(name)[0]
        send_map = {
            "document": (client.send_document, "document"),
            "video": (client.send_video, "video"),
            "audio": (client.send_audio, "audio"),
            "voice": (client.send_voice, "voice"),
        }

        send_func, param_name = send_map.get(file_type.lower(), (None, None))
        if not send_func:
            log.warning(f"[SEND FILE] ⚠️ Format file '{file_type}' tidak didukung")
            await message.reply_text(
                "❌ Format file tidak didukung.", parse_mode=ParseMode.MARKDOWN
            )
            return

        log.debug(f"[SEND FILE] 📤 Mengirim {file_type} ke Telegram API...")
        await send_func(
            chat_id=message.chat.id,
            **{param_name: file_id},
            caption=f"🎬 <b>{name_without_ext}</b>\n✅ Akses {'VIP' if vip else 'Gratis'}",
            parse_mode=ParseMode.HTML,
            protect_content=True,
            reply_markup=reply_markup,
        )

        log.debug(f"[SEND FILE] 📝 Update statistik play_count di DB")
        with get_db_cursor() as (cursor, conn):
            cursor.execute(
                """
                INSERT INTO video_stats (user_id, file_id, play_count, last_played)
                VALUES (%s, %s, 1, %s)
                ON CONFLICT (user_id, file_id)
                DO UPDATE SET
                    play_count = video_stats.play_count + 1,
                    last_played = EXCLUDED.last_played
                """,
                (user_id, file_id, now),
            )
            conn.commit()

        log.info(
            f"[SEND FILE] ✅ Selesai kirim file '{name_without_ext}' | User={user_id} | VIP={vip}"
        )

    except Exception as e:
        if "file_id" in str(e).lower():
            log.warning(
                f"[SEND FILE] ⚠️ file_id tidak valid | file_id={file_id} | User={user_id}"
            )
            await message.reply_text(
                "❌ File tidak tersedia lagi. Silakan hubungi admin.",
                parse_mode=ParseMode.HTML,
            )
        else:
            log.error(
                f"[SEND FILE] ❌ Error kirim file | Name='{name}' | User={user_id} | Error={e}",
                exc_info=True,
            )
            await message.reply_text(
                "❗ Gagal mengirim file. Silakan coba lagi.",
                parse_mode=ParseMode.HTML,
            )


async def check_duplicate_file(
    client: Client, message: Message, file_name, file_size, file_type
):
    with get_db_cursor() as (cursor, conn):
        existing = is_file_exist(cursor, file_name, file_size, file_type)
        if existing:
            free_hash, paid_hash = existing
            bot_username = await get_bot_username(client)

            caption = build_file_caption(
                file_name, file_size, free_hash, paid_hash, bot_username
            )
            await safe_reply(
                message,
                f"⚠️ File sudah ada.\n\n{caption}",
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True,
            )

            try:
                await message.delete()
                log.info(f"[check_duplicate_file] Pesan '{file_name}' dihapus.")
            except Exception as e:
                log.warning(f"[check_duplicate_file] Gagal hapus pesan: {e}")
            return True  # duplicate
    return False


def is_file_exist(cursor, file_name, file_size, file_type):
    cursor.execute(
        """
        SELECT free_hash, paid_hash
        FROM files
        WHERE file_name = %s AND file_size = %s AND file_type = %s
        """,
        (file_name, file_size, file_type),
    )
    return cursor.fetchone()


async def get_bot_username(client: Client) -> str:
    try:
        return (await client.get_me()).username or "bot"
    except Exception as e:
        log.warning(f"[get_bot_username] Fallback to default: {e}")
        return "dramaglow_bot"


def extract_file_info(message):
    try:
        if message.document:
            return (
                message.document.file_id,
                message.document.file_name or "Document",
                message.document.file_size,
                "document",
            )
        elif message.video:
            file_name = message.video.file_name or "Video"
            return (
                message.video.file_id,
                file_name,
                message.video.file_size,
                "video",
            )
        elif message.audio:
            file_name = message.audio.file_name or "Audio"
            return (
                message.audio.file_id,
                file_name,
                message.audio.file_size,
                "audio",
            )
        elif message.voice:
            return (
                message.voice.file_id,
                "Voice_Message",
                message.voice.file_size,
                "voice",
            )
        return None, None, None, None
    except Exception as e:
        log.error(f"[extract_file_info] Gagal ekstrak file info: {e}")
        return None, None, None, None


def build_file_caption(file_name, file_size, free_hash, paid_hash, bot_username):
    try:
        # Rapikan nama file dan escape karakter markdown
        nice_name = file_name or "noname"
        size_str = format_size(file_size)

        return (
            f"✅ <b>Berhasil membuat tautan Link<b>\n\n"
            f"🎬 Judul: <b>{nice_name}</b>\n"
            f"📁 Ukuran: <b>{size_str}</b>\n\n"
            f"├─ 🔗 <b>Akses Gratis:</b>\nhttps://t.me/{bot_username}?start={free_hash}\n\n"
            f"└─ 🔓 <b>Akses VIP:</b>\nhttps://t.me/{bot_username}?start={paid_hash}"
        )
    except Exception as e:
        log.error(f"[build_file_caption] Error: {e}")
        return "❌ Gagal membuat caption tautan."


def insert_show(title: str, sinopsis: str, thumbnail: str):
    from db.connect import get_db_cursor

    with get_db_cursor() as (cursor, _):
        cursor.execute(
            "INSERT INTO shows (title, sinopsis, thumbnail) VALUES (%s, %s, %s)",
            (title, sinopsis, thumbnail),
        )
