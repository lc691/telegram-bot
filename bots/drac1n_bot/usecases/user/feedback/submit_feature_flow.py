from dataclasses import dataclass
from datetime import UTC, datetime
import secrets

from configs.logging_setup import log
from ....delivery.telegram.telegram_sender import telegram_sender
from .....repository.feedback_repository import feedback_repository
from ....settings import settings


# =====================================================
# DOMAIN MODEL
# =====================================================
@dataclass(frozen=True)
class FeatureSuggestionTicket:
    id: int
    ticket_no: str
    status: str


# =====================================================
# HELPERS
# =====================================================
def _validate_suggestion(suggestion: str) -> str:
    suggestion = suggestion.strip()

    if not suggestion:
        raise ValueError("Suggestion is required")

    if len(suggestion) < 5:
        raise ValueError("Suggestion is too short")

    if len(suggestion) > 5000:
        raise ValueError("Suggestion is too long")

    return suggestion


def _generate_ticket_no(now: datetime) -> str:
    return f"FTR-{now:%y%m%d%H%M}-{secrets.randbelow(900000) + 100000}"


def _build_admin_message(ticket_no: str, user_id: int, suggestion: str, now: datetime) -> str:
    return (
        "💡 SARAN FITUR BARU\n\n"
        f"🎫 Ticket : {ticket_no}\n"
        f"👤 User ID : {user_id}\n"
        f"🕒 Waktu : {now:%d-%m-%Y %H:%M UTC}\n"
        "📌 Status : Pending\n\n"
        f"📩 Detail:\n{suggestion}"
    )


# =====================================================
# MAIN FLOW
# =====================================================
async def submit_feature_flow(
    *,
    user_id: int,
    suggestion: str,
    tracer=None,
) -> FeatureSuggestionTicket:

    text = _validate_suggestion(suggestion)
    now = datetime.now(UTC)

    if tracer:
        tracer.event("FEATURE_FLOW_START", {
            "user_id": user_id,
            "length": len(text),
        })

    ticket_no = _generate_ticket_no(now)

    ticket = feedback_repository.create_ticket(
        ticket_no=ticket_no,
        user_id=user_id,
        category="feature",
        title="Saran Fitur",
        description=text,
        status="pending",
    )

    log.info(
        "[FEEDBACK:FEATURE] user=%s ticket=%s",
        user_id,
        ticket_no,
    )

    # =================================================
    # SIDE EFFECT: ADMIN NOTIFY
    # =================================================
    try:
        await telegram_sender.send_message(
            chat_id=settings.ADMIN_FEEDBACK_CHAT_ID,
            text=_build_admin_message(ticket_no, user_id, text, now),
        )

        if tracer:
            tracer.result("ADMIN_NOTIFY_SENT")

    except Exception:
        log.exception("[FEATURE] admin notify failed")

        if tracer:
            tracer.event("ADMIN_NOTIFY_FAILED")

    if tracer:
        tracer.event("FEATURE_FLOW_END", {
            "ticket": ticket_no
        })

    return FeatureSuggestionTicket(
        id=ticket["id"],
        ticket_no=ticket["ticket_no"],
        status=ticket["status"],
    )