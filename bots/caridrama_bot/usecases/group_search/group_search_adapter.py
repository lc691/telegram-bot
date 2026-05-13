import asyncio

from typing import Dict, List

from db.connect import get_db_cursor

from ..inline_search.search_shows_usecase import search_shows
from .normalize import normalize_show_row


async def search_shows_for_group(
    *,
    query: str,
    user_id: int,
    limit: int = 10,
) -> List[Dict]:

    def _run():
        with get_db_cursor() as (cursor, _):
            result = search_shows(
                cursor=cursor,
                query=query,
                user_id=user_id,
                offset=0,
                limit=limit,
            )

            rows = []
            for row in result.rows:
                item = normalize_show_row(row)
                if item:
                    rows.append(item)

            return rows

    return await asyncio.to_thread(_run)