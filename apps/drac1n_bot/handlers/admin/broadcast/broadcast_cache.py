# broadcast_cache.py

from typing import Dict, Optional

_broadcast_cache: Dict[int, str] = {}  # user_id: text


def set_broadcast_text(user_id: int, text: str) -> None:
    """Simpan teks broadcast untuk user tertentu."""
    _broadcast_cache[user_id] = text


def get_broadcast_text(user_id: int) -> Optional[str]:
    """Ambil dan hapus teks broadcast dari cache."""
    return _broadcast_cache.pop(user_id, None)


def has_broadcast(user_id: int) -> bool:
    """Cek apakah user punya teks broadcast tersimpan."""
    return user_id in _broadcast_cache


def clear_broadcast(user_id: int) -> None:
    """Hapus teks broadcast tanpa mengambilnya."""
    _broadcast_cache.pop(user_id, None)
