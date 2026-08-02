# utils/telegram.py

def build_message_url(channel: str | None, msg_id: int) -> str:
    channel = str(channel or "")
    if channel.startswith("-100"):
        return f"https://t.me/c/{channel[4:]}/{msg_id}"
    return f"https://t.me/{channel}/{msg_id}"
