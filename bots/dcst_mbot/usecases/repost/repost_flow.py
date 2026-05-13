import asyncio
from typing import Union, List

from pyrogram.errors import ChatWriteForbidden
from pyrogram.enums import ParseMode

from .title_extractor import extract_repost_title
from .source_extractor import extract_source_label
from ...presenters.repost_presenter import build_repost_caption
from ...presenters.resolve_target import resolve_target_channels
from ...infrastructure.repost.repost_backup import backup_message
from ...infrastructure.repost.repost_repository import (
    update_main_title,
    insert_initial_views_for_title,
)
from configs.logging_setup import log


async def run_repost_flow(
    *,
    client,
    message,
    posting_channel: int,
    backup_channel: Union[str, int, List[Union[str, int]]],
):
    msg_id = message.id

    # ==========================
    # Extract Title
    # ==========================
    title = extract_repost_title(message)
    if not title:
        log.warning("[REPOST] Title tidak ditemukan.")
        return

    # ==========================
    # Extract Source
    # ==========================
    source_label = extract_source_label(message)
    if not source_label:
        log.warning("[REPOST] Source label tidak ditemukan.")
        return

    normalized_source = source_label.strip().lower()
    log.info(f"[REPOST] Source detected: {normalized_source}")

    # ==========================
    # Resolve Target Channels
    # ==========================
    targets = resolve_target_channels(source_label)
    if not targets:
        log.warning("[REPOST] Tidak ada target channel.")
        return

    log.info(f"[REPOST] Target channels: {targets}")

    # ==========================
    # Build Caption
    # ==========================
    chat = await client.get_chat(posting_channel)
    if not chat.username:
        log.error("[REPOST] Channel tidak memiliki username publik.")
        return

    link = f"https://t.me/{chat.username}/{msg_id}"
    caption = build_repost_caption(
        title=title["db"],
        subtitle="Subtitle Indonesia",
        link=link,
    )

    # ==========================
    # Backup Message
    # ==========================
    try:
        await backup_message(
            client=client,
            from_chat_id=posting_channel,
            message_id=msg_id,
            backup_channel=backup_channel,
        )
    except Exception as e:
        log.error(f"[REPOST] Backup gagal: {e}")

    # ==========================
    # Repost ke Target Channel
    # ==========================
    if not message.photo:
        log.warning("[REPOST] Pesan tidak memiliki foto.")
        return

    for target in targets:
        try:
            await client.send_photo(
                chat_id=target,
                photo=message.photo.file_id,
                caption=caption,
                parse_mode=ParseMode.HTML,
            )
            log.info(f"[REPOST] Berhasil dikirim ke {target}")
            await asyncio.sleep(2)

        except ChatWriteForbidden:
            log.warning(f"[REPOST] Tidak memiliki izin menulis ke {target}")
            continue

        except Exception as e:
            log.error(f"[REPOST] Gagal mengirim ke {target}: {e}")

    # ==========================
    # Persist Metadata
    # ==========================
    try:
        update_main_title(
            title=title["db"],
            message_id=msg_id,
        )

        insert_initial_views_for_title(
            title=title["db"],
            views=message.views or 0,
        )

        log.info(
            f"[REPOST] Metadata tersimpan | title={title['db']} | views={message.views or 0}"
        )

    except Exception as e:
        log.error(f"[REPOST] Gagal menyimpan metadata: {e}")
