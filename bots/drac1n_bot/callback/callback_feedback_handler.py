from pyrogram import Client, filters

from ..delivery.telegram.user.feedback.feedback_callback_handler import (
    feedback_callback_handler,
)


def register_feedback_callback(app: Client) -> None:

    @app.on_callback_query(filters.regex(r"^feedback:"), group=35)
    async def feedback_callback_router(client: Client, callback_query) -> None:
        try:
            await feedback_callback_handler(client, callback_query)
        except Exception as e:
            log.error("[FEEDBACK ROUTER ERROR]", exc_info=True)

            # safe fallback response
            try:
                await callback_query.answer(
                    "⚠️ Terjadi kesalahan sistem",
                    show_alert=True
                )
            except Exception:
                pass