import aiohttp
import time
from io import BytesIO

from pyrogram.enums import ParseMode

from configs.logging_setup import log
from db.posting.post_dynamic import get_active_post_channel

from ....repository.posting.post_show_utils import (
    fetch_show_by_id,
    fetch_files_by_show,
    resolve_thumbnail,
    sanitize_utf8,
)
from ....utils.caption_utils import generate_full_caption


PHOTO_CAPTION_LIMIT = 4096
TEXT_CAPTION_LIMIT = 4090
HTTP_TIMEOUT_SECONDS = 15


async def post_show_flow(*, client, show_id: int):

    # =====================================================
    # 1️⃣ Validate Channel
    # =====================================================
    posting_channel = get_active_post_channel()
    if not posting_channel:
        raise ValueError("Channel posting tidak ditemukan.")

    # =====================================================
    # 2️⃣ Fetch Show (Deterministic by ID)
    # =====================================================
    show_data = fetch_show_by_id(show_id)

    if not show_data:
        raise ValueError("Show tidak ditemukan.")

    (
        show_id,
        title,
        sinopsis,
        thumbnail,
        genre,
        hashtags,
        is_adult,
        source_code,
        source_label,
    ) = show_data

    # =====================================================
    # 3️⃣ Validate Files
    # =====================================================
    files = fetch_files_by_show(show_id)
    if not files:
        raise ValueError("Belum ada file untuk judul tersebut.")

    is_complete = any("END" in (f[0] or "").upper() for f in files)
    if is_complete and not thumbnail:
        raise ValueError("File sudah lengkap (END), tapi belum ada thumbnail.")

    # =====================================================
    # 4️⃣ Resolve Thumbnail
    # =====================================================
    final_thumb = await resolve_thumbnail(thumbnail)
    if not final_thumb:
        raise ValueError("Thumbnail tidak valid atau tidak dapat diakses.")

    # =====================================================
    # 5️⃣ Resolve Bot Username (Safe)
    # =====================================================
    try:
        me = await client.get_me()
        bot_username = me.username or "bot"
    except Exception:
        bot_username = "bot"

    # =====================================================
    # 6️⃣ Build Caption (Single Generation)
    # =====================================================
    base_caption = sanitize_utf8(
        generate_full_caption(
            title=title,
            sinopsis=sinopsis,
            genre=genre,
            hashtags=hashtags,
            files=files,
            bot_username=bot_username,
            source_code=source_code,
            source_label=source_label,
            is_adult=is_adult,
            compact=False,
        )
    )

    photo_caption = base_caption
    text_caption = base_caption

    if len(photo_caption) > PHOTO_CAPTION_LIMIT:
        log.warning(
            "[CAPTION] Photo caption over limit | show_id=%s | len=%s",
            show_id,
            len(photo_caption),
        )
        photo_caption = None

    if len(text_caption) > TEXT_CAPTION_LIMIT:
        text_caption = text_caption[:TEXT_CAPTION_LIMIT] + "..."

    # =====================================================
    # 7️⃣ Prepare Thumbnail (Handle URL Safely)
    # =====================================================
    photo_data = final_thumb

    if isinstance(final_thumb, str) and final_thumb.startswith("http"):

        headers = {"User-Agent": "Mozilla/5.0"}
        timeout = aiohttp.ClientTimeout(total=HTTP_TIMEOUT_SECONDS)

        async with aiohttp.ClientSession(
            headers=headers,
            timeout=timeout,
        ) as session:

            async with session.get(final_thumb) as resp:

                if resp.status != 200:
                    raise ValueError("Thumbnail tidak dapat diakses.")

                content = await resp.read()

        if not content:
            raise ValueError("Downloaded image is empty.")

        photo_data = BytesIO(content)
        photo_data.name = "thumb.jpg"
        photo_data.seek(0)

    # =====================================================
    # 8️⃣ Send Message (Photo → Fallback Text)
    # =====================================================
    sent_message = None
    mode = None

    if photo_caption:
        try:
            sent_message = await client.send_photo(
                chat_id=posting_channel,
                photo=photo_data,
                caption=photo_caption,
                parse_mode=ParseMode.HTML,
                disable_notification=True,
            )
            mode = "photo"

        except Exception as e:
            log.error(
                "[PHOTO ERROR] show_id=%s error=%s",
                show_id,
                str(e),
                exc_info=True,
            )

    if not sent_message:
        sent_message = await client.send_message(
            chat_id=posting_channel,
            text=text_caption,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
        )
        mode = "text"

    # =====================================================
    # 9️⃣ Generate Public Link
    # =====================================================
    link = None

    try:
        chat = await client.get_chat(posting_channel)
        if chat.username:
            link = f"https://t.me/{chat.username}/{sent_message.id}"
    except Exception:
        pass

    # =====================================================
    # 🔟 Logging
    # =====================================================
    log.info(
        "[POSTING] success | show_id=%s | mode=%s | msg_id=%s",
        show_id,
        mode,
        sent_message.id,
    )

    return {
        "title": title,
        "show_id": show_id,
        "message_id": sent_message.id,
        "link": link,
        "mode": mode,
    }
