import time
from typing import Dict

SEARCH_CACHE_TTL = 600
USER_COOLDOWN = 5

_search_cache: Dict[str, tuple] = {}
_user_last_search: Dict[int, float] = {}


def get_cached_search(query: str):
    now = time.time()
    data = _search_cache.get(query)
    if not data:
        return None

    ts, results = data
    if now - ts < SEARCH_CACHE_TTL:
        return results

    _search_cache.pop(query, None)
    return None


def set_cached_search(query: str, results):
    _search_cache[query] = (time.time(), results)


def is_user_on_cooldown(user_id: int) -> bool:
    now = time.time()
    last = _user_last_search.get(user_id, 0)
    if now - last < USER_COOLDOWN:
        return True
    _user_last_search[user_id] = now
    return False
