from ..config.settings import INLINE_LIMIT
from .inline_result_builder import (
    _inline_cache_time,
    build_inline_results,
)


class InlineSearchPresenter:

    @staticmethod
    def build(result, query: str, offset: int) -> dict:
        offset = max(int(offset or 0), 0)

        # ==================================================
        # 1️⃣ BUILD INLINE RESULTS
        # ==================================================
        results = build_inline_results(
            result=result,
            query=query,
            offset=offset,
        )

        rows = result.rows or []
        row_count = len(rows)

        # ==================================================
        # 2️⃣ SAFER PAGINATION
        # ==================================================
        has_more = row_count >= INLINE_LIMIT

        next_offset = str(offset + INLINE_LIMIT) if has_more else ""

        # ==================================================
        # 3️⃣ FINAL PAYLOAD
        # ==================================================
        return {
            "results": results,
            "is_personal": True,
            "cache_time": _inline_cache_time(result.kind),
            "next_offset": next_offset,
        }
