import asyncio
from typing import Union

from pyrogram import Client
from pyrogram.types import CallbackQuery, Message
from pyrogram.errors import FloodWait, RPCError

from configs.logging_setup import log
from ...common.display_name import get_display_name
from .ui_renderer import render_status_ui
from common.utils.ui_session_upssell import clear_user_session


STATUS_TIMEOUT_SECONDS = 8


async def handle_status_entry(
    client: Client,
    event: Union[Message, CallbackQuery],
    admin_cache,
) -> None:
    user = event.from_user
    if not user:
        return

    user_id = user.id
    username = get_display_name(user)

    log.info(
        "[STATUS] START type=%s user_id=%s",
        type(event).__name__,
        user_id,
    )

    try:
        # =====================================================
        # 🔒 WATCHDOG: cegah handler menggantung
        # =====================================================
        await asyncio.wait_for(
            render_status_ui(
                client=client,
                event=event,
                user_id=user_id,
                admin_cache=admin_cache,
            ),
            timeout=STATUS_TIMEOUT_SECONDS,
        )

        log.info("[STATUS] SUCCESS user_id=%s", user_id)

    except asyncio.TimeoutError:
        log.error(
            "[STATUS] TIMEOUT user_id=%s timeout=%ss",
            user_id,
            STATUS_TIMEOUT_SECONDS,
        )
        try:
            await event.reply_text(
                "⏳ Sistem sedang sibuk.\nSilakan coba lagi sebentar.",
                quote=True,
            )
        except Exception:
            pass

    except FloodWait as e:
        log.warning(
            "[STATUS] FloodWait user_id=%s wait=%ss",
            user_id,
            e.value,
        )
        await asyncio.sleep(e.value)

    except RPCError as e:
        log.error(
            "[STATUS] Telegram RPC error user_id=%s err=%s",
            user_id,
            e,
        )

    except Exception:
        log.exception("[STATUS] ERROR user_id=%s", user_id)

    finally:
        # =====================================================
        # 🔒 CLEANUP HARUS TAHAN ERROR
        # =====================================================
        try:
            clear_user_session(user_id)
        except Exception:
            log.exception("[STATUS] cleanup error user_id=%s", user_id)

        log.debug("[STATUS] END user_id=%s", user_id)
