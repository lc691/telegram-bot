import re
from ..types import ResultKind, SearchResult

# =========================
# Random Recommendation Cache
# =========================

MIN_TOKEN_LEN = 3


def _query_token_present(query: str, rows) -> bool:
    """
    STRICT relevancy guard:
    - 1 token  → minimal 1 match
    - >=2 token → SEMUA token harus hadir
    """

    tokens = [t.lower() for t in re.findall(r"\w+", query) if len(t) >= MIN_TOKEN_LEN]

    if not tokens:
        return False

    token_count = len(tokens)

    for row in rows:
        title = row[1]
        title_l = title.lower()

        hit = sum(1 for t in tokens if t in title_l)

        if token_count == 1 and hit >= 1:
            return True

        if token_count >= 2 and hit == token_count:
            return True

    return False


def search_shows(
    *,
    cursor,
    query: str,
    user_id: int,
    offset: int,
    limit: int,
) -> SearchResult:

    query = query.strip()
    if not query or limit <= 0:
        return SearchResult.empty(ResultKind.SEARCH)

    offset = max(offset, 0)
    fetch_limit = limit + 1  # 🔥 pagination detection

    tokens = [t.lower() for t in re.findall(r"\w+", query) if len(t) >= MIN_TOKEN_LEN]

    sim_threshold = 0.45 if len(tokens) >= 3 else 0.35

    BASE_QUERY = """
        SELECT DISTINCT ON (s.id)
            s.id,
            s.title,
            s.thumbnail_url,
            f.channel_username,
            sf.message_id
        FROM shows s
        JOIN show_files sf ON sf.show_id = s.id
        JOIN files f ON f.id = sf.file_id
        WHERE {condition}
        AND sf.message_id IS NOT NULL
        ORDER BY s.id, sf.message_id DESC
        LIMIT %s OFFSET %s
    """

    def run(condition_sql: str, value: str):
        cursor.execute(
            BASE_QUERY.format(condition=condition_sql),
            (value, fetch_limit, offset),
        )
        return cursor.fetchall() or []

    # 1️⃣ EXACT
    rows = run("LOWER(s.title) = LOWER(%s)", query)
    if rows:
        has_more = len(rows) > limit
        return SearchResult(
            rows=rows[:limit],
            kind=ResultKind.SEARCH,
            has_more=has_more,
        )

    # 2️⃣ PREFIX
    rows = run("s.title ILIKE %s", f"{query}%")
    if rows and _query_token_present(query, rows):
        has_more = len(rows) > limit
        return SearchResult(
            rows=rows[:limit],
            kind=ResultKind.SEARCH,
            has_more=has_more,
        )

    # 3️⃣ CONTAINS
    rows = run("s.title ILIKE %s", f"%{query}%")
    if rows and _query_token_present(query, rows):
        has_more = len(rows) > limit
        return SearchResult(
            rows=rows[:limit],
            kind=ResultKind.SEARCH,
            has_more=has_more,
        )

    # 4️⃣ TRIGRAM
    cursor.execute(
        """
        SELECT DISTINCT ON (s.id)
            s.id,
            s.title,
            s.thumbnail_url,
            f.channel_username,
            sf.message_id,
            similarity(s.title, %s) AS score
        FROM shows s
        JOIN show_files sf ON sf.show_id = s.id
        JOIN files f ON f.id = sf.file_id
        WHERE sf.message_id IS NOT NULL
        AND similarity(s.title, %s) > %s
        ORDER BY s.id, score DESC, sf.message_id DESC
        LIMIT %s OFFSET %s
        """,
        (query, query, sim_threshold, fetch_limit, offset),
    )

    rows = cursor.fetchall() or []

    if not rows or not _query_token_present(query, rows):
        return SearchResult.empty(ResultKind.FALLBACK)

    has_more = len(rows) > limit

    return SearchResult(
        rows=rows[:limit],
        kind=ResultKind.SEARCH,
        has_more=has_more,
    )
