# dcst_mbot/usecases/forwarded/save_forwarded_message_flow.py
from typing import Optional

from configs.logging_setup import log
from ...infrastructure.forwarded.forward_message_repository import save_forward_message
from ...utils.html_parser import parse_html_content


async def save_forwarded_message_flow(message) -> bool:
    from_user = message.from_user

    from_id = from_user.id if from_user else None

    forwarded_chat_id = None
    forward_origin_type = "-"
    forwarded_chat_title = "-"

    if message.forward_from_chat:
        forward_origin_type = message.forward_from_chat.type.value
        forwarded_chat_id = message.forward_from_chat.id
        forwarded_chat_title = message.forward_from_chat.title or "-"
    elif message.forward_from:
        forward_origin_type = "user"
        forwarded_chat_id = message.forward_from.id
        forwarded_chat_title = message.forward_from.first_name or "-"

    raw_text = message.text or message.caption or ""
    forward_text = parse_html_content(raw_text)

    media_file_id: Optional[str] = None
    if message.video:
        media_file_id = message.video.file_id
    elif message.document:
        media_file_id = message.document.file_id
    elif message.photo:
        media_file_id = message.photo[-1].file_id
    elif message.audio:
        media_file_id = message.audio.file_id

    try:
        return save_forward_message(
            original_chat_id=forwarded_chat_id,
            original_message_id=message.forward_from_message_id or 0,
            forward_from_user_id=from_id,
            forward_date=message.forward_date,
            forward_text=forward_text,
            media_file_id=media_file_id,
        )
    except Exception:
        log.exception("[FORWARD] Failed saving forwarded message")
        raise
