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
class ReportTicket:
    id: int
    ticket_no: str
    status: str


# =====================================================
# HELPERS
# =====================================================
def _validate_description(description: str) -> str:
    description = description.strip()

    if not description:
        raise ValueError("Report description is required")

    if len(description) < 10:
        raise ValueError("Report description is too short")

    if len(description) > 5000:
        raise ValueError("Report description is too long")

    return description


def _generate_ticket_no(now: datetime) -> str:
    return f"REP-{now:%y%m%d%H%M}-{secrets.randbelow(900000) + 100000}"


def _build_admin_message(ticket_no: str, user_id: int, description: str, now: datetime) -> str:
    return (
        "🐞 LAPORAN MASALAH BARU\n\n"
        f"🎫 Ticket : {ticket_no}\n"
        f"👤 User ID : {user_id}\n"
        f"🕒 Waktu : {now:%d-%m-%Y %H:%M UTC}\n"
        "📌 Status : Pending\n\n"
        f"📩 Detail:\n{description}"
    )


# =====================================================
# MAIN FLOW
# =====================================================
async def submit_report_flow(
    *,
    user_id: int,
    description: str,
    tracer=None,
) -> ReportTicket:

    desc = _validate_description(description)
    now = datetime.now(UTC)

    if tracer:
        tracer.event("REPORT_FLOW_START", {
            "user_id": user_id,
            "description_len": len(desc),
        })

    ticket_no = _generate_ticket_no(now)

    ticket = feedback_repository.create_ticket(
        ticket_no=ticket_no,
        user_id=user_id,
        category="report",
        title="Laporan Masalah",
        description=desc,
        status="pending",
    )

    log.info(
        "[REPORT] user=%s ticket=%s",
        user_id,
        ticket_no,
    )

    # =================================================
    # SIDE EFFECT: ADMIN NOTIFICATION
    # =================================================
    try:
        await telegram_sender.send_message(
            chat_id=settings.ADMIN_FEEDBACK_CHAT_ID,
            text=_build_admin_message(ticket_no, user_id, desc, now),
        )

        if tracer:
            tracer.result("ADMIN_NOTIFY_SENT")

    except Exception:
        log.exception("[REPORT] admin notify failed")

        if tracer:
            tracer.event("ADMIN_NOTIFY_FAILED")

    if tracer:
        tracer.event("REPORT_FLOW_END", {
            "ticket": ticket_no
        })

    return ReportTicket(
        id=ticket["id"],
        ticket_no=ticket["ticket_no"],
        status=ticket["status"],
    )