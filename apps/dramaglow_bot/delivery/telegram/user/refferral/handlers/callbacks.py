from pyrogram.types import CallbackQuery

from configs.logging_setup import log
from shared.utils.menu_utils import edit_menu

from ..audit import audit_log
from ..usecases.referral_leaderboard import show_referral_leaderboard
from ..usecases.referral_link import show_referral_link_menu
from ..usecases.referral_stats import show_referral_stats_menu
from ..withdraw import show_withdraw_menu
from ..menu import show_referral_menu


async def referral_callback_handler(_, cq: CallbackQuery):
    user = cq.from_user
    if not user:
        return

    user_id = user.id
    data = cq.data

    await cq.answer()

    handlers_map = {
        "ref_link": ("MENU", show_referral_link_menu, "OPEN_LINK"),
        "ref_stats": ("MENU", show_referral_stats_menu, "OPEN_STATS"),
        "ref_withdraw": ("MENU", show_withdraw_menu, "OPEN_WITHDRAW"),
        "ref_leaderboard": ("MENU", show_referral_leaderboard, None),
        "ref_menu": ("MENU", show_referral_menu, None),
        "ref_close": ("MENU_CLOSE", None, "CLOSE_MENU"),
    }

    action_type, handler, log_action = handlers_map.get(data, (None, None, None))

    if log_action:
        audit_log(log_action, user_id)

    # ===============================
    # MENU CLOSE
    # ===============================
    if action_type == "MENU_CLOSE":
        await edit_menu(
            event=cq,
            text="✅ Menu ditutup",
        )
        return

    # ===============================
    # MENU
    # ===============================
    if action_type == "MENU" and handler:
        await handler(event=cq)
        return

    # ===============================
    # ACTION
    # ===============================
    if action_type == "ACTION" and handler:
        await handler(cq)
        return

    log.warning("[REFERRAL][CB] unknown action data=%s user_id=%s", data, user_id)
