from typing import Union

from pyrogram.types import Message, CallbackQuery
from pyrogram.enums import ParseMode

from configs.logging_setup import log
from common.utils_new.menu_utils import edit_menu

from ..usecases.status_flow import run_status_flow
from ..presenters.status_presenter import build_status_payload


async def show_status_menu(
    event: Union[Message, CallbackQuery],
    admin_cache,
) -> None:
    """
    STATUS MENU
    - EDIT ONLY
    - single-message UI
    """

    user = event.from_user
    if not user:
        return

    user_id = user.id

    result = run_status_flow(
        user_id=user_id,
        user=user,
        admin_cache=admin_cache,
    )

    # ===============================
    # BLOCKED → NOTIFICATION
    # ===============================
    if result.blocked:
        if isinstance(event, CallbackQuery):
            await event.answer(result.message, show_alert=False)
        else:
            await event.reply_text(result.message)
        return

    payload = build_status_payload(result.context)

    try:
        await edit_menu(
            event=event,
            text=payload["text"],
            markup=payload["reply_markup"],
            parse_mode=payload.get("parse_mode", ParseMode.HTML),
        )

        log.info("[STATUS][MENU] render success user_id=%s", user_id)

    except Exception:
        log.exception("[STATUS][MENU] render error user_id=%s", user_id)
        await edit_menu(
            event=event,
            text="⚠️ Gagal memuat status.\nSilakan coba lagi.",
        )
