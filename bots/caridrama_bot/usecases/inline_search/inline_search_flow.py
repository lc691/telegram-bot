from db.connect import get_db_cursor
from configs.logging_setup import log

from .services.search_service import search_shows
from .services.auto_trending_shows import get_auto_trending_shows
from .services.popular_shows import get_popular_shows

from .types import ResultKind, SearchResult
from .policies import detect_inline_mode
from ...config.settings import INLINE_LIMIT


def run_inline_search_flow(*, user_id: int, query: str, offset: int) -> SearchResult:

    offset = max(int(offset or 0), 0)

    log.info(
        "[INLINE_FLOW] start user=%s query=%r offset=%s",
        user_id,
        query,
        offset,
    )

    result: SearchResult | None = None

    with get_db_cursor() as (cursor, _):

        # 1️⃣ EMPTY QUERY → TRENDING
        if not query:
            log.info("[INLINE_FLOW] mode=TRENDING (empty query)")
            result = get_auto_trending_shows(
                cursor=cursor,
                limit=INLINE_LIMIT,
                offset=offset,
            )

        else:
            # 2️⃣ MODE DETECTION
            kind = detect_inline_mode(query)
            log.info("[INLINE_FLOW] mode=%s", kind)

            if kind == ResultKind.TRENDING:
                result = get_auto_trending_shows(
                    cursor=cursor,
                    limit=INLINE_LIMIT,
                    offset=offset,
                )

            elif kind == ResultKind.POPULAR:
                result = get_popular_shows(
                    cursor=cursor,
                    limit=INLINE_LIMIT,
                    offset=offset,
                )

            else:
                # 3️⃣ SEARCH
                log.info("[INLINE_FLOW] mode=SEARCH query=%r", query)
                result = search_shows(
                    cursor=cursor,
                    query=query,
                    user_id=user_id,
                    offset=offset,
                    limit=INLINE_LIMIT,
                )

    # ==================================================
    # 🔒 HARD GUARD FINAL
    # ==================================================
    if result is None:
        log.error(
            "[INLINE_FLOW] invariant broken: result is None user=%s query=%r",
            user_id,
            query,
        )
        return SearchResult.empty()

    # Safety: ensure has_more exists (backward compatibility)
    if not hasattr(result, "has_more"):
        result.has_more = False  # type: ignore

    # ==================================================
    # LOGGING OUTCOME
    # ==================================================
    log.info(
        "[INLINE_FLOW] result kind=%s rows=%s has_more=%s query=%r",
        result.kind,
        len(result.rows),
        result.has_more,
        query,
    )

    return result
