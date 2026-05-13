# app/usecases/vip/show_entry.py
from typing import Union

from pyrogram import Client
from pyrogram.types import CallbackQuery, Message

from common.utils.message_utils import safe_send_or_edit
from configs.logging_setup import log

from ....presenters.user.common.display_name import get_display_name
from ....presenters.user.vip.keyboards import vip_home_keyboard


async def show_vip_entry(
    client: Client,
    event: Union[Message, CallbackQuery],
    fallback: str | None = None,
):
    user = event.from_user
    user_id = user.id
    username = get_display_name(user, fallback)

    log.info("[VIP][ENTRY] user_id=%s", user_id)

    try:
        await safe_send_or_edit(
            client=client,
            user_id=user_id,
            text="Klik tombol di bawah untuk melihat pilihan paket VIP 👇",
            markup=vip_home_keyboard(),
            event=event,
        )

    except Exception:
        log.exception("[VIP][ENTRY] failed user_id=%s", user_id)

        if isinstance(event, CallbackQuery):
            await event.answer(
                "❌ Gagal menampilkan menu VIP.",
                show_alert=True,
            )
