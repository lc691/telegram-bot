import asyncio

from pyrogram.enums import ParseMode

from shared.utils.callback_helpers import safe_reply
from config import UPLOAD_DELAY
from configs.logging_setup import log
from database.file_management import save_file_metadata
from ....utils.episode_policy import resolve_is_paid_from_filename
from ....utils.media_handler import (
    build_file_caption,
    check_duplicate_file,
    extract_file_info,
)
from .new_file_helpers import (
    get_cached_bot_username,
    resolve_channel_username,
    resolve_show_id_safe,
)

# optional flood guard (ringan)
_NEW_FILE_SEM = asyncio.Semaphore(2)


async def process_new_file(client, message):
    async with _NEW_FILE_SEM:
        msg_id = message.id

        # =========================
        # 1️⃣ Resolve channel
        # =========================
        chat_uname = resolve_channel_username(message.chat)

        # =========================
        # 2️⃣ Extract file info
        # =========================
        file_id, file_name, file_size, file_type = extract_file_info(message)
        if not all([file_id, file_name, file_size, file_type]):
            await safe_reply(message, "❌ File tidak valid.")
            return

        log.info(
            "[NEW_FILE] incoming " "name='%s' size=%s type=%s channel=%s msg_id=%s",
            file_name,
            file_size,
            file_type,
            chat_uname,
            msg_id,
        )

        # =========================
        # 3️⃣ Duplicate check (FAST FAIL)
        # =========================
        try:
            is_dup = await check_duplicate_file(
                client, message, file_name, file_size, file_type
            )
        except Exception:
            log.exception("[NEW_FILE] duplicate check failed msg_id=%s", msg_id)
            return

        if is_dup:
            log.info("[NEW_FILE] duplicate skipped '%s'", file_name)
            return

        # =========================
        # 4️⃣ Resolve show_id (SAFE)
        # =========================
        show_id = resolve_show_id_safe(file_name)

        # =========================
        # 5️⃣ Save metadata (ATOMIC)
        # =========================
        is_paid = resolve_is_paid_from_filename(file_name)

        # 🔒 GUARD DEFENSIF (WAJIB JIKA FORMAT FILE TIDAK KONSISTEN)
        if is_paid is None:
            log.warning(
                "[NEW_FILE] cannot resolve is_paid name='%s'",
                file_name,
            )
            is_paid = True  # default aman → PAID

        log.info(
            "[NEW_FILE] episode policy name='%s' is_paid=%s",
            file_name,
            is_paid,
        )

        result = save_file_metadata(
            file_id=file_id,
            file_name=file_name,
            channel_username=chat_uname,
            file_type=file_type,
            file_size=file_size,
            show_id=show_id,
            is_paid=is_paid,  # 🔥 FINAL VALUE
        )

        if not result:
            await safe_reply(message, "⚠️ File sudah ada.")
            return

        free_hash, paid_hash = result

        log.info(
            "[NEW_FILE] saved " "name='%s' show_id=%s free=%s paid=%s",
            file_name,
            show_id,
            free_hash,
            paid_hash,
        )

        # =========================
        # 6️⃣ Build caption
        # =========================
        bot_username = await get_cached_bot_username(client)

        caption = build_file_caption(
            file_name=file_name,
            file_size=file_size,
            free_hash=free_hash,
            paid_hash=paid_hash,
            bot_username=bot_username,
        )

        # =========================
        # 7️⃣ Reply
        # =========================
        await safe_reply(
            message,
            caption,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
        )

        # =========================
        # 8️⃣ Cleanup (best effort)
        # =========================
        try:
            await message.delete()
        except Exception:
            log.debug(
                "[NEW_FILE] delete skipped msg_id=%s (no permission / already deleted)",
                msg_id,
            )

        if UPLOAD_DELAY:
            log.debug("[NEW_FILE] cooldown %.2fs", UPLOAD_DELAY)
            await asyncio.sleep(UPLOAD_DELAY)
