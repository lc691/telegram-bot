import random
import time
from typing import Dict, List

from database.connection import get_dict_cursor

# =========================
# Random Recommendation Cache
# =========================

_RANDOM_CACHE: dict[int, dict] = {}
_CACHE_DURATION = 300
_MAX_CACHE_USERS = 1000
MIN_TOKEN_LEN = 3


def get_random_recommendations(
    *,
    user_id: int,
    limit: int = 10,
    offset: int = 0,
) -> List[Dict]:
    """
    RANDOM RECOMMENDATION

    Filosofi:
    - Random berbasis show, bukan file
    - Cache per user untuk konsistensi pagination
    - TTL-based eviction
    - Tidak bias ke ID kecil

    Flow:
    1. Ambil semua show_id yang punya message_id valid
    2. Shuffle sekali per TTL
    3. Slice berdasarkan offset
    4. Fetch detail hanya untuk show_id terpilih
    """

    if limit <= 0:
        return []

    offset = max(offset, 0)
    now = time.time()

    cache = _RANDOM_CACHE.get(user_id)
    if cache and now - cache["timestamp"] < _CACHE_DURATION:
        show_ids = cache["data"]
    else:
        with get_dict_cursor() as (cursor, _):
            cursor.execute(
                """
                SELECT DISTINCT sf.show_id
                FROM show_files sf
                WHERE sf.message_id IS NOT NULL
                """
            )
            show_ids = [row["show_id"] for row in cursor.fetchall() or []]

        if not show_ids:
            return []

        random.shuffle(show_ids)

        _RANDOM_CACHE[user_id] = {
            "data": show_ids,
            "timestamp": now,
        }

        # eviction
        if len(_RANDOM_CACHE) > _MAX_CACHE_USERS:
            oldest = min(
                _RANDOM_CACHE,
                key=lambda uid: _RANDOM_CACHE[uid]["timestamp"],
            )
            _RANDOM_CACHE.pop(oldest, None)

    selected_ids = show_ids[offset : offset + limit]

    if not selected_ids:
        return []

    # Fetch detail hanya untuk show yang diperlukan
    with get_dict_cursor() as (cursor, _):
        cursor.execute(
            """
            SELECT DISTINCT ON (s.id)
                s.id,
                s.title,
                s.thumbnail_url,
                f.channel_username,
                sf.message_id
            FROM shows s
            JOIN show_files sf ON sf.show_id = s.id
            JOIN files f ON f.id = sf.file_id
            WHERE s.id = ANY(%s)
              AND sf.message_id IS NOT NULL
            ORDER BY s.id, sf.message_id DESC
            """,
            (selected_ids,),
        )
        rows = cursor.fetchall() or []

    return rows
