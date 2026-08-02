# app/services/vip/click_lock.py
import time

_CLICK_LOCK: dict[int, float] = {}

def is_click_locked(user_id: int, ttl: float = 3.0) -> bool:
    now = time.monotonic()

    # cleanup ringan
    for uid, ts in list(_CLICK_LOCK.items()):
        if now - ts > ttl * 2:
            _CLICK_LOCK.pop(uid, None)

    last = _CLICK_LOCK.get(user_id, 0)
    if now - last < ttl:
        return True

    _CLICK_LOCK[user_id] = now
    return False
