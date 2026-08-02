from typing import Union

from pyrogram.types import Message, CallbackQuery
from pyrogram.enums import ParseMode
from pyrogram.errors import RPCError, FloodWait

from configs.logging_setup import log
from shared.utils.menu_utils import edit_menu
from ..ui.keyboards import vip_home_keyboard


async def show_vip_entry(
    *, event: Union[Message, CallbackQuery], display_name: str | None = None
):
    """
    VIP ENTRY MENU
    - EDIT ONLY
    - single-message UI
    """

    user = event.from_user
    if not user:
        log.warning("[VIP][ENTRY] ignored (no from_user)")
        return

    user_id = user.id

    log.info(
        "[VIP][ENTRY] render start user_id=%s type=%s",
        user_id,
        type(event).__name__,
    )

    text = (
        "🔒 <b>Konten VIP terkunci</b>\n\n"
        "═══════✦✧✦═══════\n"
        "🎬 Buka semua episode VIP\n"
        "⚡ Tanpa delay\n"
        "✨ Tanpa iklan mengganggu\n"
        "🚀 Streaming tanpa batas\n"
        "═══════✦✧✦═══════\n"

    )

    try:
        await edit_menu(
            event=event,
            text=text,
            markup=vip_home_keyboard(),
            parse_mode=ParseMode.HTML,
        )

        log.info("[VIP][ENTRY] render success user_id=%s", user_id)

    except FloodWait as e:
        log.warning(
            "[VIP][ENTRY] FloodWait user_id=%s wait=%ss",
            user_id,
            e.value,
        )

    except RPCError as e:
        log.error(
            "[VIP][ENTRY] Telegram RPC error user_id=%s err=%s",
            user_id,
            e,
        )

    except Exception:
        log.exception("[VIP][ENTRY] fatal error user_id=%s", user_id)
        await edit_menu(
            event=event,
            text="⚠️ Terjadi kesalahan.\nSilakan coba lagi.",
        )
