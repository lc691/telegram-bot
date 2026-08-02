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
class RequestDramaTicket:
    id: int
    ticket_no: str
    drama_title: str
    status: str


# =====================================================
# HELPERS
# =====================================================
def _validate_title(title: str) -> str:
    title = title.strip()

    if not title:
        raise ValueError("Drama title is required")

    if len(title) < 2:
        raise ValueError("Drama title is too short")

    if len(title) > 200:
        raise ValueError("Drama title is too long")

    return title


def _generate_ticket_no(now: datetime) -> str:
    return f"REQ-{now:%y%m%d%H%M}-{secrets.randbelow(900000) + 100000}"


def _build_admin_message(ticket_no: str, user_id: int, title: str, now: datetime) -> str:
    return (
        "🎬 REQUEST DRAMA BARU\n\n"
        f"🎫 Ticket : {ticket_no}\n"
        f"👤 User ID : {user_id}\n"
        f"🎭 Drama : {title}\n"
        f"🕒 Waktu : {now:%d-%m-%Y %H:%M UTC}\n"
        "📌 Status : Pending"
    )


# =====================================================
# MAIN FLOW
# =====================================================
async def submit_request_drama_flow(
    *,
    user_id: int,
    drama_title: str,
    tracer=None,
) -> RequestDramaTicket:

    title = _validate_title(drama_title)

    now = datetime.now(UTC)

    if tracer:
        tracer.event("REQUEST_DRAMA_FLOW_START", {
            "user_id": user_id,
            "title": title,
        })

    ticket_no = _generate_ticket_no(now)

    ticket = feedback_repository.create_ticket(
        ticket_no=ticket_no,
        user_id=user_id,
        category="request_drama",
        title=title,
        description=title,
        status="pending",
    )

    log.info(
        "[REQUEST_DRAMA] user=%s ticket=%s title=%s",
        user_id,
        ticket_no,
        title,
    )

    # =================================================
    # SIDE EFFECT: ADMIN NOTIFICATION
    # =================================================
    try:
        await telegram_sender.send_message(
            chat_id=settings.ADMIN_FEEDBACK_CHAT_ID,
            text=_build_admin_message(ticket_no, user_id, title, now),
        )

        if tracer:
            tracer.result("ADMIN_NOTIFY_SENT")

    except Exception:
        log.exception("[REQUEST_DRAMA] admin notify failed")

        if tracer:
            tracer.event("ADMIN_NOTIFY_FAILED")

    if tracer:
        tracer.event("REQUEST_DRAMA_FLOW_END", {
            "ticket": ticket_no
        })

    return RequestDramaTicket(
        id=ticket["id"],
        ticket_no=ticket["ticket_no"],
        drama_title=title,
        status=ticket["status"],
    )