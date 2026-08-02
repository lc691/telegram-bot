from ..services.search_service import search_shows

from ..services.auto_trending_shows import (
    get_auto_trending_shows,
)

class SearchStrategy:

    name = "SEARCH"

    def execute(
        self,
        *,
        cursor,
        user_id,
        query,
        offset,
        limit,
    ):

        result = search_shows(
            cursor=cursor,
            query=query,
            user_id=user_id,
            offset=offset,
            limit=limit,
        )

        # SMART FALLBACK
        if not result.rows:

            return get_auto_trending_shows(
                cursor=cursor,
                limit=limit,
                offset=offset,
            )

        return result