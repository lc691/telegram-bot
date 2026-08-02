from typing import List

from ...domain.show_repository import (
    search_exact,
    search_fuzzy,
    search_prefix,
)

from .services.random_rekomendations import get_random_recommendations

from ..analytics.track_query_miss import track_miss_if_needed
from .types import ResultKind, SearchResult
from ..group_search.normalize import normalize_show_row


# ==================================================
# INTERNAL NORMALIZER
# ==================================================


def _normalize_rows(rows) -> List[dict]:
    """Pastikan semua row mengikuti kontrak FINAL."""
    normalized = []

    for r in rows:
        try:
            item = normalize_show_row(r)
        except Exception:
            # Hard guard — jangan rusak flow search
            continue

        if item:
            normalized.append(item)

    return normalized


# ==================================================
# MAIN SEARCH
# ==================================================


def search_shows(
    *,
    cursor,
    query: str,
    user_id: int,
    offset: int,
    limit: int,
) -> SearchResult:

    # =============================
    # HARD PARAM GUARD
    # =============================
    if limit <= 0:
        return SearchResult(rows=[], kind=ResultKind.SEARCH)

    if offset < 0:
        offset = 0

    query = (query or "").strip()

    # =============================
    # RANDOM (EMPTY QUERY)
    # =============================
    if not query:
        return SearchResult(
            rows=get_random_recommendations(
                cursor,
                user_id=user_id,
                offset=offset,
                limit=limit,
            ),
            kind=ResultKind.RANDOM,
        )

    # ==================================================
    # SEARCH PIPELINE (EXACT → PREFIX → FUZZY)
    # ==================================================
    search_pipeline = (
        search_exact,
        search_prefix,
        search_fuzzy,
    )

    for strategy in search_pipeline:
        try:
            rows = strategy(cursor, query, limit, offset)
        except Exception:
            continue  # skip strategy if repo layer fails

        if rows:
            normalized = _normalize_rows(rows)
            if normalized:
                return SearchResult(
                    rows=normalized,
                    kind=ResultKind.SEARCH,
                )

    # ==================================================
    # MISS → ANALYTICS + RANDOM FALLBACK
    # ==================================================
    try:
        track_miss_if_needed(
            cursor=cursor,
            query=query,
            user_id=user_id,
            source="inline",
        )
    except Exception:
        pass  # analytics failure must not break UX

    return SearchResult(
        rows=get_random_recommendations(
            cursor,
            user_id=user_id,
            offset=offset,
            limit=limit,
        ),
        kind=ResultKind.FALLBACK,
    )
