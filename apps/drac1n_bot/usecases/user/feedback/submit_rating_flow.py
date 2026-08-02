from dataclasses import dataclass
from datetime import UTC, datetime

from configs.logging_setup import log
from ....delivery.telegram.telegram_sender import telegram_sender
from .....repository.feedback_repository import feedback_repository
from ....settings import settings


# =====================================================
# DOMAIN MODEL
# =====================================================
@dataclass(frozen=True)
class RatingResult:
    rating: int


# =====================================================
# HELPERS
# =====================================================
def _validate_rating(rating: int) -> int:
    if not isinstance(rating, int):
        raise ValueError("Rating must be an integer")

    if not (1 <= rating <= 5):
        raise ValueError("Rating must be between 1 and 5")

    return rating


def _build_admin_message(user_id: int, rating: int, now: datetime) -> str:
    stars = "⭐" * rating

    return (
        "⭐ RATING BARU\n\n"
        f"👤 User ID : {user_id}\n"
        f"📊 Rating : {rating}/5\n"
        f"{stars}\n"
        f"🕒 Waktu : {now:%d-%m-%Y %H:%M UTC}\n"
    )


# =====================================================
# MAIN FLOW
# =====================================================
async def submit_rating_flow(
    *,
    user_id: int,
    rating: int,
    tracer=None,
) -> RatingResult:

    value = _validate_rating(rating)
    now = datetime.now(UTC)

    if tracer:
        tracer.event("RATING_FLOW_START", {
            "user_id": user_id,
            "rating": value,
        })

    feedback_repository.create_rating(
        user_id=user_id,
        rating=value,
    )

    log.info(
        "[FEEDBACK:RATING] user=%s rating=%s",
        user_id,
        value,
    )

    # =================================================
    # SIDE EFFECT: ADMIN NOTIFY
    # =================================================
    try:
        await telegram_sender.send_message(
            chat_id=settings.ADMIN_FEEDBACK_CHAT_ID,
            text=_build_admin_message(user_id, value, now),
        )

        if tracer:
            tracer.result("ADMIN_NOTIFY_SENT")

    except Exception:
        log.exception("[RATING] admin notify failed")

        if tracer:
            tracer.event("ADMIN_NOTIFY_FAILED")

    if tracer:
        tracer.event("RATING_FLOW_END", {
            "rating": value
        })

    return RatingResult(rating=value)