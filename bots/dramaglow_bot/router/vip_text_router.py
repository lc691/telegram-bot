from pyrogram import Client
from pyrogram.types import Message

from bots.dramaglow_bot.handlers.vip.add_vip.vip_add_step import handle_vip_add_step
from common.utils.callback_helpers import safe_reply
from common.utils.vip_state_manager import VipStateManager
from configs.logging_setup import log


async def handle_vip_text(
    client: Client, message: Message, is_admin: bool
) -> bool | None:
    user_id = message.from_user.id
    vip_state = VipStateManager(user_id, source_bot=getattr(client, "bot_name", "glow"))

    if not is_admin:
        return None

    try:
        if vip_state.get_vip_add_step():
            return await handle_vip_add_step(client, message, vip_state)
    except Exception as e:
        log.exception(f"[VIP_FLOW] ❌ Gagal proses FSM VIP user {user_id}: {e}")
        await safe_reply(
            message,
            "❌ Terjadi kesalahan saat memproses flow VIP. Silakan coba lagi.",
        )
    finally:
        # Pastikan state di-clear agar tidak menggantung
        vip_state.clear()

    return None
