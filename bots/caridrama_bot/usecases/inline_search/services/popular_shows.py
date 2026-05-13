from ..types import ResultKind, SearchResult


def get_popular_shows(
    *,
    cursor,
    limit: int,
    offset: int,
) -> SearchResult:

    if limit <= 0:
        return SearchResult.empty(ResultKind.POPULAR)

    fetch_limit = limit + 1

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
        WHERE sf.message_id IS NOT NULL
        ORDER BY s.id, sf.message_id DESC
        LIMIT %s OFFSET %s
        """,
        (fetch_limit, offset),
    )

    raw_rows = cursor.fetchall() or []

    # =============================
    # PAGINATION DETECTION
    # =============================
    has_more = len(raw_rows) > limit
    rows = raw_rows[:limit]

    return SearchResult(
        rows=rows,
        kind=ResultKind.POPULAR if rows else ResultKind.FALLBACK,
        has_more=has_more,
    )
