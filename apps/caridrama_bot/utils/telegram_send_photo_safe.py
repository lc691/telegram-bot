import io
import requests

from pyrogram import Client

from configs.logging_setup import log


async def send_photo_safe(
    client: Client,
    chat_id: int,
    photo_url: str,
    caption: str | None = None,
    reply_markup=None,
    parse_mode=None,
):

    log.info(
        "[SAFE_PHOTO] download url=%s",
        photo_url,
    )

    resp = requests.get(
        photo_url,
        timeout=20,
        headers={
            "User-Agent": "Mozilla/5.0",
        },
    )

    resp.raise_for_status()

    log.info(
        "[SAFE_PHOTO] downloaded bytes=%s content_type=%s",
        len(resp.content),
        resp.headers.get("content-type"),
    )

    photo = io.BytesIO(resp.content)

    photo.name = "thumb.jpg"

    return await client.send_photo(
        chat_id=chat_id,
        photo=photo,
        caption=caption,
        parse_mode=parse_mode,
        reply_markup=reply_markup,
    )
