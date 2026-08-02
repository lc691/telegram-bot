# utils/callback_guard.py
import time

_CLICK_CACHE: dict[str, float] = {}
_TTL = 2.0  # detik


def is_double_click(key: str) -> bool:
    now = time.monotonic()
    last = _CLICK_CACHE.get(key)

    if last and now - last < _TTL:
        return True

    _CLICK_CACHE[key] = now
    return False
