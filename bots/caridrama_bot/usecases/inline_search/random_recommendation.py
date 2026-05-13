import random
import time

from ...presenters.channel_validasi import is_valid_telegram_username

RANDOM_CACHE: dict[int, dict] = {}
CACHE_DURATION = 30


def get_random_recommendations(
    cursor,
    *,
    user_id: int,
    offset: int,
    limit: int,
):
    now = time.time()
    cache = RANDOM_CACHE.get(user_id)

    if cache and now - cache["timestamp"] < CACHE_DURATION:
        data = cache["data"]

    else:
        cursor.execute(
            """
            SELECT
                s.id               AS show_id,
                s.title,
                f.channel_username,
                MAX(sf.message_id) AS message_id
            FROM shows s
            JOIN show_files sf ON sf.show_id = s.id
            JOIN files f ON f.id = sf.file_id
            WHERE sf.message_id IS NOT NULL
            GROUP BY s.id, s.title, f.channel_username
            """
        )

        rows = cursor.fetchall()
        data = []

        for r in rows:
            show_id = r[0]
            title = r[1]
            channel_username = r[2]
            message_id = r[3]

            # =============================
            # HARD GUARD — KONTRAK FINAL
            # =============================
            if not show_id or not title:
                continue

            if not isinstance(message_id, int):
                continue

            if not isinstance(channel_username, str):
                continue

            if not is_valid_telegram_username(channel_username):
                continue

            data.append(
                {
                    "show_id": show_id,
                    "title": title,
                    "channel_username": channel_username,
                    "message_id": message_id,
                    # placeholder kontrak global
                    "channel_id": None,
                }
            )

        random.shuffle(data)

        RANDOM_CACHE[user_id] = {
            "data": data,
            "timestamp": now,
        }

    return data[offset : offset + limit]
