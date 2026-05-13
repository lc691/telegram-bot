from .types import ResultKind

_MODE_MAP: dict[str, ResultKind] = {
    "trending": ResultKind.TRENDING,
    "🔥": ResultKind.TRENDING,
    "trend": ResultKind.TRENDING,
    "popular": ResultKind.POPULAR,
    "⭐": ResultKind.POPULAR,
    "pop": ResultKind.POPULAR,
}


def detect_inline_mode(query: str) -> ResultKind:
    q = (query or "").lower().strip()
    if not q:
        return ResultKind.TRENDING
    return _MODE_MAP.get(q, ResultKind.SEARCH)


# def apply_similarity_threshold(cursor):
#     cursor.execute("SET LOCAL pg_trgm.similarity_threshold = 0.2;")
