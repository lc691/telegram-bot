import json

from pyrogram import Client
from pyrogram.enums import ParseMode
from pyrogram.types import Message

from bots.drac1n_bot.handlers.vip.add_vip.vip_ask_user_id import handle_ask_user_id
from common.utils.admin_notifier import notify_admin_error
from common.utils.callback_helpers import safe_reply
from common.utils.escape_markdown import escape_md
from common.utils.fsm_helpers import validate_step_from_message
from common.utils.vip_state_manager import VipStateManager
from configs.logging_setup import log


async def handle_vip_add_step(client: Client, message: Message, state: VipStateManager):
    user_input = message.text.strip()
    user_id = message.from_user.id
    bot_name = client.name
    current_step = state.get_vip_add_step()

    if not current_step:
        log.warning(f"[VIP_ADD] ⛔ Tidak ada step aktif untuk user_id={user_id}")
        return

    # ✅ Validasi FSM dimulai oleh bot yang sama
    source_bot = state.get_temp("source_bot")
    try:
        source_bot = json.loads(source_bot) if source_bot else None
    except Exception:
        source_bot = None

    if source_bot and bot_name != source_bot:
        safe_text = escape_md(source_bot)
        return await safe_reply(
            message,
            f"⚠️ Proses VIP sedang berlangsung di bot <code>@{safe_text}</code>.\n"
            f"Silakan lanjutkan proses di sana.",
            parse_mode=ParseMode.HTML,
        )

    log.info(
        f"[VIP_ADD] user_id={user_id}, bot={bot_name}, step={current_step}, input={user_input}"
    )

    try:
        if not await validate_step_from_message(
            message, state, expected_step=current_step
        ):

            return

        match current_step:
            case "vip_add:ask_user_id":
                await handle_ask_user_id(client, message, user_input, state)

            case "vip_add:waiting_package":
                await safe_reply(
                    message, "📌 Silakan pilih paket VIP dari tombol yang tersedia."
                )

            case _:
                log.warning(
                    f"[VIP_ADD] ⛔ Step tidak dikenali user_id={user_id}: {current_step}"
                )
                await safe_reply(
                    message, "❌ Langkah tidak dikenali. Silakan ulangi proses."
                )
                state.clear()

    except Exception as e:
        log.error(f"[VIP_ADD] ❌ Error user {user_id}: {e}", exc_info=True)
        await notify_admin_error(client, f"[VIP_ADD] ❌ Error user {user_id}: {e}")
        await safe_reply(message, "❌ Terjadi kesalahan saat memproses input Anda.")
