import time
from typing import Dict, Optional, Tuple

# Cache: user_id -> (chat_id, message_id, timestamp)
_message_cache: Dict[int, Tuple[int, int, float]] = {}

CACHE_TTL_SECONDS = 10  # detik


def set_last_message(user_id: int, chat_id: int, message_id: int) -> None:
    """
    Simpan pesan terakhir user (PRIVATE CHAT ONLY).
    """
    if user_id != chat_id:
        return  # jangan cache group/channel

    _message_cache[user_id] = (chat_id, message_id, time.time())


def get_last_message(user_id: int) -> Optional[Tuple[int, int]]:
    """
    Ambil pesan terakhir user jika masih valid.
    """
    data = _message_cache.get(user_id)
    if not data:
        return None

    chat_id, message_id, ts = data

    if time.time() - ts > CACHE_TTL_SECONDS:
        _message_cache.pop(user_id, None)
        return None

    return chat_id, message_id


def clear_last_message(user_id: int) -> None:
    """
    Hapus cache pesan user.
    """
    _message_cache.pop(user_id, None)
