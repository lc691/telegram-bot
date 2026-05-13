from pyrogram import Client
from pyrogram.types import InlineQuery

from configs.logging_setup import log
from bots.caridrama_bot.usecases.inline_search.inline_search_flow import (
    run_inline_search_flow,
)
from bots.caridrama_bot.presenters.inline_search_presenter import InlineSearchPresenter


def register_inline_search(app: Client) -> None:
    @app.on_inline_query()
    async def inline_search_handler(_: Client, iq: InlineQuery):
        user = iq.from_user
        if not user:
            return

        user_id = user.id
        query = (iq.query or "").strip()

        # ==================================================
        # 1️⃣ OFFSET PARSE (DEFENSIVE)
        # ==================================================
        try:
            offset = int(iq.offset or 0)
        except ValueError:
            offset = 0

        log.info(
            "[INLINE] start user=%s query=%r offset=%s",
            user_id,
            query,
            offset,
        )

        # ==================================================
        # 2️⃣ RUN INLINE SEARCH FLOW
        # ==================================================
        try:
            result = run_inline_search_flow(
                user_id=user_id,
                query=query,
                offset=offset,
            )
        except Exception:
            log.exception(
                "[INLINE] FLOW ERROR user=%s query=%r",
                user_id,
                query,
            )
            return

        # ==================================================
        # 3️⃣ BUILD + ANSWER
        # ==================================================
        try:
            payload = InlineSearchPresenter.build(
                result,
                query,
                offset,
            )
            await iq.answer(**payload)

            log.info(
                "[INLINE] answered user=%s results=%s next_offset=%s",
                user_id,
                len(payload.get("results", [])),
                payload.get("next_offset"),
            )

        except Exception as e:
            # Telegram bisa reject answer (timeout / duplicate / empty)
            log.debug(
                "[INLINE] ANSWER SKIPPED user=%s reason=%s",
                user_id,
                type(e).__name__,
            )
