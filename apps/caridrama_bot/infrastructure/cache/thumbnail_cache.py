# bots/caridrama_bot/cache/thumbnail_cache.py

THUMBNAIL_CACHE: dict[int, str] = {}  # key = show_id, value = path file


def get_thumbnail(show_id: int) -> str | None:
    return THUMBNAIL_CACHE.get(show_id)


def set_thumbnail(show_id: int, path: str) -> None:
    THUMBNAIL_CACHE[show_id] = path


def clear_cache() -> None:
    THUMBNAIL_CACHE.clear()
