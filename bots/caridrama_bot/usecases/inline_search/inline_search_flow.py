from time import perf_counter
from uuid import uuid4

from db.connect import get_db_cursor
from configs.logging_setup import log

from .services.search_service import search_shows
from .services.auto_trending_shows import get_auto_trending_shows
from .services.popular_shows import get_popular_shows

from .types import ResultKind, SearchResult
from .policies import detect_inline_mode
from ...config.settings import INLINE_LIMIT


# =========================================================
# LOGGING HELPER
# =========================================================

def log_event(stage: str, **kwargs):

    payload = " ".join(
        f"{k}={v!r}"
        for k, v in kwargs.items()
    )

    log.info("[%s] %s", stage, payload)


# =========================================================
# INLINE SEARCH FLOW
# =========================================================

def run_inline_search_flow(
    *,
    user_id: int,
    query: str,
    offset: int,
) -> SearchResult:

    started = perf_counter()

    request_id = uuid4().hex[:8]

    query = (query or "").strip()

    offset = max(int(offset or 0), 0)

    log_event(
        "INLINE_REQ",
        rid=request_id,
        user=user_id,
        query=query,
        offset=offset,
    )

    result: SearchResult | None = None

    mode = "UNKNOWN"

    try:

        db_started = perf_counter()

        with get_db_cursor() as (cursor, _):

            # =================================================
            # EMPTY QUERY -> TRENDING
            # =================================================

            if not query:

                mode = "TRENDING"

                result = get_auto_trending_shows(
                    cursor=cursor,
                    limit=INLINE_LIMIT,
                    offset=offset,
                )

            else:

                # =============================================
                # MODE DETECTION
                # =============================================

                detected = detect_inline_mode(query)

                mode = str(detected)

                # =============================================
                # TRENDING
                # =============================================

                if detected == ResultKind.TRENDING:

                    result = get_auto_trending_shows(
                        cursor=cursor,
                        limit=INLINE_LIMIT,
                        offset=offset,
                    )

                # =============================================
                # POPULAR
                # =============================================

                elif detected == ResultKind.POPULAR:

                    result = get_popular_shows(
                        cursor=cursor,
                        limit=INLINE_LIMIT,
                        offset=offset,
                    )

                # =============================================
                # SEARCH
                # =============================================

                else:

                    result = search_shows(
                        cursor=cursor,
                        query=query,
                        user_id=user_id,
                        offset=offset,
                        limit=INLINE_LIMIT,
                    )

        db_ms = round((perf_counter() - db_started) * 1000)

        # =====================================================
        # HARD GUARD
        # =====================================================

        if result is None:

            log.error(
                "[INLINE_BROKEN] rid=%s user=%s query=%r",
                request_id,
                user_id,
                query,
            )

            return SearchResult.empty()

        # backward compatibility
        if not hasattr(result, "has_more"):
            result.has_more = False  # type: ignore

        total_ms = round((perf_counter() - started) * 1000)

        # =====================================================
        # SUCCESS LOG
        # =====================================================

        log_event(
            "INLINE_RESULT",
            rid=request_id,
            mode=mode,
            kind=result.kind,
            rows=len(result.rows),
            has_more=result.has_more,
            db_ms=db_ms,
            total_ms=total_ms,
        )

        # =====================================================
        # SLOW QUERY DETECTION
        # =====================================================

        if total_ms >= 500:

            log.warning(
                (
                    "[INLINE_SLOW] "
                    "rid=%s query=%r mode=%s took=%sms"
                ),
                request_id,
                query,
                mode,
                total_ms,
            )

        return result

    except Exception:

        total_ms = round((perf_counter() - started) * 1000)

        log.exception(
            (
                "[INLINE_ERROR] "
                "rid=%s user=%s query=%r "
                "offset=%s mode=%s took=%sms"
            ),
            request_id,
            user_id,
            query,
            offset,
            mode,
            total_ms,
        )

        return SearchResult.empty()