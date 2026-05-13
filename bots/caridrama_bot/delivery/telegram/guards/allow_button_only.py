from ....config.settings import ALLOWED_CHAT_IDS


async def allow_button_only(message) -> bool:
    """
    True → boleh tampilkan tombol
    False → diam
    """
    if message.chat.id not in ALLOWED_CHAT_IDS:
        return False

    # Auto posting (channel / anon admin)
    if message.sender_chat:
        return True

    return False
