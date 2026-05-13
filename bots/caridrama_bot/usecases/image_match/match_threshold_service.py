import time
from .match_threshold_repository import load_match_thresholds

_CACHE: dict | None = None
_CACHE_AT = 0.0
_TTL = 60  # detik


def get_match_thresholds() -> dict:
    global _CACHE, _CACHE_AT

    now = time.time()
    if _CACHE and (now - _CACHE_AT) < _TTL:
        return _CACHE

    _CACHE = load_match_thresholds()
    _CACHE_AT = now
    return _CACHE
