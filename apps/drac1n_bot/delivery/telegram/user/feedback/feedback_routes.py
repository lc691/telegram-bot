from typing import Callable, Dict

from pyrogram.enums import ParseMode
from pyrogram.types import CallbackQuery

from shared.utils.admin_state_manager import AdminStateManager
from .....repository.feedback_repository import feedback_repository


# =====================================================
# ROUTE REGISTRY
# =====================================================
ROUTES: Dict[str, Callable] = {}


def register(route: str):
    def wrapper(fn: Callable):
        ROUTES[route] = fn
        return fn
    return wrapper


# =====================================================
# STATUS MAP
# =====================================================
STATUS_LABELS = {
    "pending": "⏳ Menunggu Review",
    "resolved": "✅ Selesai",
    "rejected": "❌ Ditolak",
}


# =====================================================
# HANDLERS
# =====================================================

@register("feedback:request_drama")
async def handle_request_drama(state: AdminStateManager, callback_query: CallbackQuery):
    state.set_step(
        AdminStateManager.FEEDBACK_STEP,
        AdminStateManager.FEEDBACK_REQUEST_DRAMA,
    )

    await callback_query.message.edit_text(
        "🎬 <b>REQUEST DRAMA</b>\n\nSilakan kirim judul drama.",
        parse_mode=ParseMode.HTML,
    )
    return True


@register("feedback:report")
async def handle_report(state: AdminStateManager, callback_query: CallbackQuery):
    state.set_step(
        AdminStateManager.FEEDBACK_STEP,
        AdminStateManager.FEEDBACK_REPORT,
    )

    await callback_query.message.edit_text(
        "🐞 <b>LAPOR MASALAH</b>\n\nJelaskan masalahnya.",
        parse_mode=ParseMode.HTML,
    )
    return True


@register("feedback:feature")
async def handle_feature(state: AdminStateManager, callback_query: CallbackQuery):
    state.set_step(
        AdminStateManager.FEEDBACK_STEP,
        AdminStateManager.FEEDBACK_FEATURE,
    )

    await callback_query.message.edit_text(
        "💡 <b>SARAN FITUR</b>",
        parse_mode=ParseMode.HTML,
    )
    return True


@register("feedback:rating")
async def handle_rating(state: AdminStateManager, callback_query: CallbackQuery):
    state.set_step(
        AdminStateManager.FEEDBACK_STEP,
        AdminStateManager.FEEDBACK_RATING,
    )

    await callback_query.message.edit_text(
        "⭐ <b>RATING 1-5</b>",
        parse_mode=ParseMode.HTML,
    )
    return True


@register("feedback:my_ticket")
async def handle_my_ticket(state: AdminStateManager, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id

    tickets = feedback_repository.get_user_tickets(
        user_id=user_id,
        limit=10,
    )

    if not tickets:
        await callback_query.message.edit_text(
            "📊 Belum ada tiket.",
            parse_mode=ParseMode.HTML,
        )
        return True

    lines = ["📊 <b>STATUS TIKET SAYA</b>", ""]

    for t in tickets:
        status = STATUS_LABELS.get(t.get("status"), t.get("status", "-"))

        lines.extend([
            f"🎫 {t.get('ticket_no', '-')}",
            f"📂 {t.get('category', '-')}",
            f"📝 {t.get('title', '-')}",
            f"{status}",
            "",
        ])

    await callback_query.message.edit_text(
        "\n".join(lines),
        parse_mode=ParseMode.HTML,
    )
    return True
