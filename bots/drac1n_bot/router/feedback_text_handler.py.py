from pyrogram import Client
from pyrogram.types import Message

from common.utils.admin_state_manager import AdminStateManager
from configs.logging_setup import log

from ..usecases.user.feedback.submit_request_drama_flow import submit_request_drama_flow
from ..usecases.user.feedback.submit_report_flow import submit_report_flow
from ..user.feedback.submit_feature_flow import submit_feature_flow
from ..usecases.user.feedback.submit_rating_flow import submit_rating_flow


# =====================================================
# SAFE UTIL
# =====================================================
def _safe_text(text: str) -> str:
    return (text or "").strip()


# =====================================================
# STATE RESET (DETACHED FROM None / JSON AMBIGUITY)
# =====================================================
def _reset_feedback_state(state: AdminStateManager):
    state.set_step(AdminStateManager.FEEDBACK_STEP, "")


# =====================================================
# HANDLERS (STATE → ACTION MAP)
# =====================================================
async def _handle_request_drama(state, user_id, text, message, tracer):
    if len(text) < 2:
        await message.reply_text("❌ Judul drama terlalu pendek.")
        return True

    ticket = await submit_request_drama_flow(
        user_id=user_id,
        drama_title=text,
    )

    _reset_feedback_state(state)

    await message.reply_text(
        "✅ Request berhasil dikirim\n\n"
        f"🎫 Ticket: {ticket.ticket_no}\n"
        f"🎬 Drama: {text}"
    )

    if tracer:
        tracer.result("REQUEST_DRAMA_DONE", {"ticket": ticket.ticket_no})

    return True


async def _handle_report(state, user_id, text, message, tracer):
    if len(text) < 10:
        await message.reply_text("❌ Mohon jelaskan masalah lebih detail.")
        return True

    ticket = await submit_report_flow(
        user_id=user_id,
        description=text,
    )

    _reset_feedback_state(state)

    await message.reply_text(
        "✅ Laporan dikirim\n\n"
        f"🎫 Ticket: {ticket.ticket_no}"
    )

    if tracer:
        tracer.result("REPORT_DONE", {"ticket": ticket.ticket_no})

    return True


async def _handle_feature(state, user_id, text, message, tracer):
    if len(text) < 5:
        await message.reply_text("❌ Saran terlalu pendek.")
        return True

    ticket = await submit_feature_flow(
        user_id=user_id,
        suggestion=text,
    )

    _reset_feedback_state(state)

    await message.reply_text(
        "✅ Saran terkirim\n\n"
        f"🎫 Ticket: {ticket.ticket_no}"
    )

    if tracer:
        tracer.result("FEATURE_DONE", {"ticket": ticket.ticket_no})

    return True


async def _handle_rating(state, user_id, text, message, tracer):
    try:
        rating = int(text)
    except ValueError:
        await message.reply_text("❌ Masukkan angka 1–5.")
        return True

    if rating < 1 or rating > 5:
        await message.reply_text("❌ Rating harus 1–5.")
        return True

    await submit_rating_flow(
        user_id=user_id,
        rating=rating,
    )

    _reset_feedback_state(state)

    await message.reply_text(f"⭐ Terima kasih ({rating}/5)")

    if tracer:
        tracer.result("RATING_DONE", {"rating": rating})

    return True


# =====================================================
# FSM ROUTER (PURE DISPATCH TABLE)
# =====================================================
FEEDBACK_ROUTER = {
    AdminStateManager.FEEDBACK_REQUEST_DRAMA: _handle_request_drama,
    AdminStateManager.FEEDBACK_REPORT: _handle_report,
    AdminStateManager.FEEDBACK_FEATURE: _handle_feature,
    AdminStateManager.FEEDBACK_RATING: _handle_rating,
}


# =====================================================
# MAIN ENTRY (DETERMINISTIC FSM ENTRYPOINT)
# =====================================================
async def handle_feedback_text(
    client: Client,
    message: Message,
    tracer=None,
) -> bool:

    if not message.from_user:
        return False

    user_id = message.from_user.id
    text = _safe_text(message.text)

    state = AdminStateManager(user_id)

    feedback_state = state.get_step_strict(AdminStateManager.FEEDBACK_STEP)

    if not feedback_state:
        return False

    if tracer:
        tracer.event("FEEDBACK_START", {
            "user_id": user_id,
            "state": feedback_state,
            "text_len": len(text),
        })

    handler = FEEDBACK_ROUTER.get(feedback_state)

    if handler is None:
        log.warning(f"[FSM] Unknown feedback state: {feedback_state}")
        return False

    try:
        return await handler(state, user_id, text, message, tracer)

    except Exception as e:
        log.error(f"[FEEDBACK ERROR] user={user_id} err={e}", exc_info=True)

        _reset_feedback_state(state)

        if tracer:
            tracer.event("FEEDBACK_ERROR", {"error": str(e)})

        await message.reply_text(
            "⚠️ Terjadi kesalahan saat memproses masukan Anda."
        )

        return True