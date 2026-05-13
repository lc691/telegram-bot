import asyncio
from typing import Union

from pyrogram import Client
from pyrogram.enums import ParseMode
from pyrogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)
from pyrogram.errors import FloodWait, RPCError

from common.utils.callback_helpers import safe_answer
from common.utils.message_tracker import (
    save_last_sent_message,
    try_edit_last_message,
)
from configs.logging_setup import log
from ...common.display_name import get_display_name


async def render_status_ui(
    client: Client,
    event: Union[Message, CallbackQuery],
    user_id: int,
    text: str,
) -> None:
    # =====================================================
    # 🔒 HARD GUARD USER
    # =====================================================
    user = event.from_user
    if not user:
        log.warning("[STATUS][UI] ignored (no from_user)")
        return

    username = get_display_name(user)

    markup = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("💎 Beli VIP", callback_data="vip_menu")],
            [InlineKeyboardButton("↩️ Kembali", callback_data="back_to_vip_home")],
        ]
    )

    # =====================================================
    # 🔒 CALLBACK HARUS SELALU DIJAWAB
    # =====================================================
    if isinstance(event, CallbackQuery):
        try:
            await safe_answer(event)
        except Exception:
            log.debug("[STATUS][UI] safe_answer failed user=%s", username)

    # =====================================================
    # 🔒 COBA EDIT TERAKHIR (TERISOLASI)
    # =====================================================
    try:
        result = await try_edit_last_message(
            client,
            user_id,
            text=text,
            markup=markup,
            parse_mode=ParseMode.HTML,
        )
    except Exception:
        log.exception("[STATUS][UI] edit attempt failed user=%s", username)
        result = None

    if result == "edited":
        log.info("[STATUS][UI] edited user=%s", username)
        return

    # =====================================================
    # 🔒 KIRIM PESAN BARU
    # =====================================================
    try:
        if isinstance(event, CallbackQuery):
            msg = await event.message.reply_text(
                text,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True,
                reply_markup=markup,
            )
        else:
            msg = await event.reply_text(
                text,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True,
                reply_markup=markup,
            )
    except FloodWait as e:
        log.warning(
            "[STATUS][UI] FloodWait send user=%s wait=%ss",
            username,
            e.value,
        )
        await asyncio.sleep(e.value)
        return
    except RPCError as e:
        log.error("[STATUS][UI] Telegram error user=%s err=%s", username, e)
        return
    except Exception:
        log.exception("[STATUS][UI] send failed user=%s", username)
        return

    # =====================================================
    # 🔒 SIMPAN STATE (TIDAK BOLEH FATAL)
    # =====================================================
    try:
        save_last_sent_message(user_id, msg)
    except Exception:
        log.exception("[STATUS][UI] save_last_message failed user=%s", username)

    log.info("[STATUS][UI] sent user=%s", username)
