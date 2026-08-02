import asyncio

from pyrogram.enums import ParseMode

from common.utils.callback_helpers import safe_reply
from config import UPLOAD_DELAY
from configs.logging_setup import log
from db.file_management import save_file_metadata

from ....utils.episode_policy import (
    resolve_is_paid_from_filename,
)
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


_NEW_FILE_SEM = asyncio.Semaphore(2)


async def process_new_file(
    client,
    message,
):

    async with _NEW_FILE_SEM:

        file_info = extract_file_info(message)

        if not all(file_info):

            await safe_reply(
                message,
                "❌ File tidak valid.",
            )

            return

        (
            file_id,
            file_name,
            file_size,
            file_type,
        ) = file_info

        try:

            is_duplicate = (
                await check_duplicate_file(
                    client,
                    message,
                    file_name,
                    file_size,
                    file_type,
                )
            )

        except Exception:

            log.exception(
                "[NEW_FILE] duplicate check failed msg_id=%s",
                message.id,
            )

            return

        if is_duplicate:

            log.debug(
                "[NEW_FILE] duplicate skipped '%s'",
                file_name,
            )

            return

        is_paid = (
            resolve_is_paid_from_filename(
                file_name
            )
        )

        if is_paid is None:

            log.warning(
                "[NEW_FILE] cannot resolve policy '%s'",
                file_name,
            )

            is_paid = True

        result = save_file_metadata(
            file_id=file_id,
            file_name=file_name,
            channel_username=resolve_channel_username(
                message.chat
            ),
            file_type=file_type,
            file_size=file_size,
            show_id=resolve_show_id_safe(
                file_name
            ),
            is_paid=is_paid,
        )

        if not result:

            return

        free_hash, paid_hash = result

        log.info(
            "[NEW_FILE] saved '%s'",
            file_name,
        )

        caption = build_file_caption(
            file_name=file_name,
            file_size=file_size,
            free_hash=free_hash,
            paid_hash=paid_hash,
            bot_username=(
                await get_cached_bot_username(
                    client
                )
            ),
        )

        await safe_reply(
            message,
            caption,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
        )

        try:

            await message.delete()

        except Exception:

            pass

        if UPLOAD_DELAY:

            await asyncio.sleep(
                UPLOAD_DELAY
            )