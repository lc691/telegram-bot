from ..types import ResultKind, SearchResult


def get_auto_trending_shows(
    *,
    cursor,
    limit: int,
    offset: int,
) -> SearchResult:

    if limit <= 0:
        return SearchResult.empty(ResultKind.TRENDING)

    offset = max(offset, 0)

    fetch_limit = limit + 1

    cursor.execute(
        """
        SELECT
            show_id,
            title,
            thumbnail_url,
            channel_username,
            message_id
        FROM trending_cache
        WHERE
            title IS NOT NULL
            AND message_id IS NOT NULL
        ORDER BY rank ASC
        LIMIT %s OFFSET %s
        """,
        (fetch_limit, offset),
    )

    raw_rows = cursor.fetchall() or []

    has_more = len(raw_rows) > limit

    rows = raw_rows[:limit]

    return SearchResult(
        rows=rows,
        kind=ResultKind.TRENDING if rows else ResultKind.FALLBACK,
        has_more=has_more,
    )