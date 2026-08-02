from __future__ import annotations

import socket
from html import escape
from io import BytesIO
from typing import Optional

from dataclasses import (
    dataclass,
    asdict,
)

import aiohttp
from pyrogram.enums import ParseMode
from pyrogram.errors import RPCError

from configs.logging_setup import log
from database.repositories.posting.post_dynamic import get_active_post_channel

from ....repository.posting.post_show_utils import (
    fetch_show_by_id,
    fetch_files_by_show,
    resolve_thumbnail,
    sanitize_utf8,
)

from ....utils.caption_utils import generate_full_caption
from .enhace_photo import enhance_thumbnail
# =========================================================
# CONSTANTS
# =========================================================

PHOTO_CAPTION_LIMIT = 4096
TEXT_CAPTION_LIMIT = 4090
HTTP_TIMEOUT_SECONDS = 15

# =========================================================
# GLOBAL HTTP SESSION
# =========================================================

_http_session: Optional[aiohttp.ClientSession] = None

# =========================================================
# DATA MODELS
# =========================================================


@dataclass(slots=True)
class ShowData:
    show_id: int
    title: str
    sinopsis: str
    thumbnail: Optional[str]
    genre: Optional[str]
    hashtags: Optional[str]
    is_adult: bool
    source_code: Optional[str]
    source_label: Optional[str]


@dataclass(slots=True)
class PostResult:
    title: str
    show_id: int
    message_id: int
    link: Optional[str]
    mode: str


# =========================================================
# SESSION
# =========================================================


async def get_http_session() -> aiohttp.ClientSession:

    global _http_session

    if _http_session and not _http_session.closed:
        return _http_session

    timeout = aiohttp.ClientTimeout(
        total=HTTP_TIMEOUT_SECONDS
    )

    connector = aiohttp.TCPConnector(
        family=socket.AF_INET,
        ttl_dns_cache=300,
        limit=50,
    )

    _http_session = aiohttp.ClientSession(
        headers={
            "User-Agent": "Mozilla/5.0"
        },
        timeout=timeout,
        connector=connector,
    )

    return _http_session


# =========================================================
# VALIDATION
# =========================================================


def validate_posting_channel() -> str:

    posting_channel = get_active_post_channel()

    if not posting_channel:
        raise ValueError(
            "Channel posting tidak ditemukan."
        )

    return posting_channel


# =========================================================
# SHOW FETCH
# =========================================================


def get_show_data(show_id: int) -> ShowData:

    row = fetch_show_by_id(show_id)

    if not row:
        raise ValueError(
            "Show tidak ditemukan."
        )

    return ShowData(
        show_id=row[0],
        title=row[1],
        sinopsis=row[2],
        thumbnail=row[3],
        genre=row[4],
        hashtags=row[5],
        is_adult=row[6],
        source_code=row[7],
        source_label=row[8],
    )


# =========================================================
# FILE VALIDATION
# =========================================================


def validate_show_files(show_id: int):

    files = fetch_files_by_show(show_id)

    if not files:
        raise ValueError(
            "Belum ada file untuk judul tersebut."
        )

    return files


def validate_completion(
    *,
    files,
    thumbnail,
):

    is_complete = any(
        "END" in ((f[0] or "").upper())
        for f in files
    )

    if is_complete and not thumbnail:

        raise ValueError(
            "File sudah lengkap (END), "
            "tapi belum ada thumbnail."
        )


# =========================================================
# CAPTION
# =========================================================


async def resolve_bot_username(client) -> str:

    try:

        me = await client.get_me()

        return me.username or "bot"

    except Exception:

        return "bot"


def build_caption(
    *,
    show: ShowData,
    files,
    bot_username: str,
) -> str:

    caption = generate_full_caption(
        title=escape(show.title or ""),
        sinopsis=escape(show.sinopsis or ""),
        genre=escape(show.genre or ""),
        hashtags=show.hashtags,
        files=files,
        bot_username=bot_username,
        source_code=show.source_code,
        source_label=show.source_label,
        is_adult=show.is_adult,
        compact=False,
    )

    return sanitize_utf8(caption)


def normalize_caption(
    caption: str,
) -> tuple[Optional[str], str]:

    photo_caption = caption
    text_caption = caption

    # =========================================
    # PHOTO LIMIT
    # =========================================

    if len(photo_caption) > PHOTO_CAPTION_LIMIT:

        log.warning(
            "[CAPTION] photo caption over limit "
            "| len=%s",
            len(photo_caption),
        )

        photo_caption = None

    # =========================================
    # TEXT LIMIT
    # =========================================

    if len(text_caption) > TEXT_CAPTION_LIMIT:

        text_caption = (
            text_caption[:TEXT_CAPTION_LIMIT]
            + "..."
        )

    return (
        photo_caption,
        text_caption,
    )


# =========================================================
# THUMBNAIL
# =========================================================


async def prepare_thumbnail(
    thumbnail,
):

    final_thumb = await resolve_thumbnail(
        thumbnail
    )

    if not final_thumb:

        raise ValueError(
            "Thumbnail tidak valid "
            "atau tidak dapat diakses."
        )

    # =========================================
    # LOCAL / RAW
    # =========================================

    if not (
        isinstance(final_thumb, str)
        and final_thumb.startswith("http")
    ):

        log.info(
            "[THUMB] local thumbnail source"
        )

        return final_thumb

    # =========================================
    # REMOTE URL
    # =========================================

    log.info(
        "[THUMB] downloading "
        "| url=%s",
        final_thumb,
    )

    session = await get_http_session()

    try:

        async with session.get(
            final_thumb,
            ssl=False,
        ) as resp:

            if resp.status != 200:

                raise ValueError(
                    "Thumbnail gagal diakses "
                    f"| status={resp.status}"
                )

            content = await resp.read()

        if not content:

            raise ValueError(
                "Downloaded image empty."
            )

        log.info(
            "[THUMB] downloaded "
            "| bytes=%s",
            len(content),
        )

        bio = BytesIO(content)

        bio.name = "thumb.jpg"

        bio.seek(0)

        return bio

    except aiohttp.ClientError as e:

        log.exception(
            "[THUMB][ERROR] %s",
            str(e),
        )

        return None


# =========================================================
# SENDERS
# =========================================================


async def send_photo_post(
    *,
    client,
    posting_channel,
    photo,
    caption,
):

    log.info(
        "[PHOTO] sending "
        "| caption_len=%s",
        len(caption),
    )

    result = await client.send_photo(
        chat_id=posting_channel,
        photo=photo,
        caption=caption,
        parse_mode=ParseMode.HTML,
        disable_notification=True,
    )

    log.info(
        "[PHOTO] success "
        "| msg_id=%s",
        result.id,
    )

    return result


async def send_text_post(
    *,
    client,
    posting_channel,
    text,
):

    return await client.send_message(
        chat_id=posting_channel,
        text=text,
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
        disable_notification=True,
    )


# =========================================================
# PUBLIC LINK
# =========================================================


async def build_public_link(
    *,
    client,
    posting_channel,
    message_id,
):

    try:

        chat = await client.get_chat(
            posting_channel
        )

        if chat.username:

            return (
                f"https://t.me/"
                f"{chat.username}/"
                f"{message_id}"
            )

    except RPCError:

        return None

    return None


# =========================================================
# MAIN FLOW
# =========================================================


async def post_show_flow(
    *,
    client,
    show_id: int,
):

    photo_data = None

    try:

        # =====================================
        # CHANNEL
        # =====================================

        posting_channel = (
            validate_posting_channel()
        )

        # =====================================
        # SHOW
        # =====================================

        show = get_show_data(show_id)

        # =====================================
        # FILES
        # =====================================

        files = validate_show_files(
            show.show_id
        )

        validate_completion(
            files=files,
            thumbnail=show.thumbnail,
        )

        # =====================================
        # BOT
        # =====================================

        bot_username = (
            await resolve_bot_username(
                client
            )
        )

        # =====================================
        # CAPTION
        # =====================================

        caption = build_caption(
            show=show,
            files=files,
            bot_username=bot_username,
        )

        (
            photo_caption,
            text_caption,
        ) = normalize_caption(
            caption
        )

        # =====================================
        # THUMBNAIL
        # =====================================

        photo_data = await prepare_thumbnail(
            show.thumbnail
        )

        photo_data = await enhance_thumbnail(
            photo_data
        )

        # =====================================
        # SEND PHOTO
        # =====================================

        sent_message = None
        mode = "text"

        if photo_caption and photo_data:

            try:

                sent_message = (
                    await send_photo_post(
                        client=client,
                        posting_channel=posting_channel,
                        photo=photo_data,
                        caption=photo_caption,
                    )
                )

                mode = "photo"

            except RPCError as e:

                log.exception(
                    "[PHOTO ERROR] "
                    "show_id=%s error=%s",
                    show.show_id,
                    str(e),
                )

                log.warning(
                    "[PHOTO] fallback=text "
                    "| show_id=%s",
                    show.show_id,
                )

        # =====================================
        # FALLBACK TEXT
        # =====================================

        if not sent_message:

            sent_message = (
                await send_text_post(
                    client=client,
                    posting_channel=posting_channel,
                    text=text_caption,
                )
            )

            mode = "text"

        # =====================================
        # PUBLIC LINK
        # =====================================

        link = await build_public_link(
            client=client,
            posting_channel=posting_channel,
            message_id=sent_message.id,
        )

        # =====================================
        # LOG
        # =====================================

        log.info(
            "[POSTING] success "
            "| show_id=%s "
            "| mode=%s "
            "| msg_id=%s",
            show.show_id,
            mode,
            sent_message.id,
        )

        return asdict(
            PostResult(
                title=show.title,
                show_id=show.show_id,
                message_id=sent_message.id,
                link=link,
                mode=mode,
            )
        )

    finally:

        if isinstance(photo_data, BytesIO):

            photo_data.close()
