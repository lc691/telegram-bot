from ..config.settings import INLINE_LIMIT
from .inline_result_builder import (
    _inline_cache_time,
    build_inline_results,
)

from configs.logging_setup import log


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

        log.info(
            "[INLINE_PRESENT] built_results=%s",
            len(results),
        )

        # ==================================================
        # 2️⃣ PAGINATION
        # ==================================================
        has_more = bool(getattr(result, "has_more", False))

        next_offset = (
            str(offset + INLINE_LIMIT)
            if has_more
            else ""
        )

        log.info(
            "[INLINE_PRESENT] has_more=%s next_offset=%r",
            has_more,
            next_offset,
        )

        # ==================================================
        # 3️⃣ FINAL PAYLOAD
        # ==================================================
        payload = {
            "results": results,

            # disable aggressive cache while debugging
            "cache_time": 0,

            "is_personal": True,
            "next_offset": next_offset,
        }

        log.info(
            "[INLINE_PRESENT] payload_ready results=%s",
            len(results),
        )

        return payload