from configs.logging_setup import log

from ...domain.analytics_repository import track_query_miss


def track_miss_if_needed(
    *,
    cursor,
    query: str,
    user_id: int,
    source: str,
):
    if not query.strip():
        return

    try:
        track_query_miss(
            cursor,
            query=query,
            user_id=user_id,
            source=source,
        )
    except Exception:
        log.exception("[ANALYTICS] Failed to track query miss")
