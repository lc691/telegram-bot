import re
from ..types import ResultKind, SearchResult

MIN_TOKEN_LEN = 2
MAX_RESULTS_BUFFER = 5


# =====================================================
# TOKENIZER
# =====================================================

def _tokenize(text: str) -> list[str]:
    return [
        t.lower()
        for t in re.findall(r"\w+", text)
        if len(t) >= MIN_TOKEN_LEN
    ]


# =====================================================
# STRICT TOKEN VALIDATION
# =====================================================

def _is_relevant(query: str, title: str) -> bool:
    """
    Relevancy rules:

    - 1 token  -> minimal token muncul
    - 2 token+ -> semua token wajib ada
    """

    query_tokens = _tokenize(query)

    if not query_tokens:
        return False

    title_l = title.lower()

    matched = sum(1 for t in query_tokens if t in title_l)

    if len(query_tokens) == 1:
        return matched >= 1

    return matched == len(query_tokens)


# =====================================================
# SEARCH SCORE
# =====================================================

def _score_title(query: str, title: str, trigram_score: float = 0.0) -> float:
    """
    Manual ranking layer.

    Priority:

    1000 -> exact
    700  -> prefix
    500  -> contains
    + token bonus
    + trigram bonus
    """

    query_l = query.lower().strip()
    title_l = title.lower().strip()

    score = 0.0

    # EXACT
    if title_l == query_l:
        score += 1000

    # PREFIX
    elif title_l.startswith(query_l):
        score += 700

    # CONTAINS
    elif query_l in title_l:
        score += 500

    query_tokens = _tokenize(query_l)

    for token in query_tokens:
        if token in title_l:
            score += 40

            # Strong bonus for word prefix
            if re.search(rf"\b{re.escape(token)}", title_l):
                score += 20

    # Short title bonus
    score += max(0, 30 - abs(len(title_l) - len(query_l)))

    # Trigram similarity bonus
    score += trigram_score * 100

    return score


# =====================================================
# MAIN SEARCH
# =====================================================

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

    tokens = _tokenize(query)

    if not tokens:
        return SearchResult.empty(ResultKind.SEARCH)

    # Adaptive trigram threshold
    if len(tokens) >= 4:
        sim_threshold = 0.55
    elif len(tokens) == 3:
        sim_threshold = 0.45
    else:
        sim_threshold = 0.35

    fetch_limit = limit + MAX_RESULTS_BUFFER

    # =====================================================
    # SINGLE PROFESSIONAL QUERY
    # =====================================================

    cursor.execute(
        """
        SELECT DISTINCT ON (s.id)
            s.id,
            s.title,
            s.thumbnail_url,
            f.channel_username,
            sf.message_id,
            similarity(LOWER(s.title), LOWER(%s)) AS score
        FROM shows s
        JOIN show_files sf ON sf.show_id = s.id
        JOIN files f ON f.id = sf.file_id
        WHERE sf.message_id IS NOT NULL
        AND (
            LOWER(s.title) = LOWER(%s)
            OR s.title ILIKE %s
            OR s.title ILIKE %s
            OR similarity(LOWER(s.title), LOWER(%s)) >= %s
        )
        ORDER BY
            s.id,
            score DESC,
            sf.message_id DESC
        LIMIT %s OFFSET %s
        """,
        (
            query,
            query,
            f"{query}%",
            f"%{query}%",
            query,
            sim_threshold,
            fetch_limit,
            offset,
        ),
    )

    rows = cursor.fetchall() or []

    if not rows:
        return SearchResult.empty(ResultKind.FALLBACK)

    # =====================================================
    # PYTHON RELEVANCY FILTER
    # =====================================================

    filtered = []

    for row in rows:
        (
            show_id,
            title,
            thumb,
            channel,
            message_id,
            trigram_score,
        ) = row

        if not _is_relevant(query, title):
            continue

        final_score = _score_title(
            query=query,
            title=title,
            trigram_score=trigram_score,
        )

        filtered.append(
            (
                final_score,
                (
                    show_id,
                    title,
                    thumb,
                    channel,
                    message_id,
                ),
            )
        )

    if not filtered:
        return SearchResult.empty(ResultKind.FALLBACK)

    # =====================================================
    # FINAL SORTING
    # =====================================================

    filtered.sort(
        key=lambda x: (
            x[0],
            -len(x[1][1]),
        ),
        reverse=True,
    )

    final_rows = [row for _, row in filtered]

    has_more = len(final_rows) > limit

    return SearchResult(
        rows=final_rows[:limit],
        kind=ResultKind.SEARCH,
        has_more=has_more,
    )
