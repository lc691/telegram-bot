# rate_limit.py
from time import time

from ....config.settings import RATE_LIMIT, WINDOW

rate_limit_cache = {}


def is_rate_limited(user_id: int) -> bool:
    now = time()
    windowed = [t for t in rate_limit_cache.get(user_id, []) if now - t < WINDOW]
    windowed.append(now)
    rate_limit_cache[user_id] = windowed
    return len(windowed) > RATE_LIMIT
