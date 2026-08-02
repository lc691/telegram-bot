# === handlers/text_router/admin_text_router.py ===

from typing import Optional

from pyrogram import Client
from pyrogram.types import Message

from apps.drac1n_bot.handlers.admin.add.admin_add import handle_regular_step
from apps.drac1n_bot.handlers.admin.remove.admin_remove import handle_admin_remove_step
from apps.drac1n_bot.handlers.admin.source.add_source_step import handle_add_source_step
from apps.drac1n_bot.handlers.admin.update.admin_update import handle_admin_update_step
from apps.drac1n_bot.ui.dashboard import send_dashboard
from shared.utils.admin_state_manager import AdminStateManager
from shared.utils.state_helper import cancel_all_states
from shared.utils.vip_state_manager import VipStateManager
from configs.logging_setup import log


async def handle_admin_text(
    client: Client, message: Message, is_admin: bool
) -> Optional[bool]:
    user_id = message.from_user.id
    text = message.text.strip()

    admin_state = AdminStateManager(user_id)
    vip_state = VipStateManager(
        user_id, source_bot=getattr(client, "bot_name", "drac1n")
    )

    if admin_state.is_expired():
        log.warning(f"[SESSION] Sesi user {user_id} kedaluwarsa.")
        admin_state.clear()
        vip_state.clear()
        await message.reply_text("⏰ Sesi Anda telah kedaluwarsa.")
        await send_dashboard(source=message, is_callback=False)
        return True

    regular_step = admin_state.get_step("regular_step")
    if is_admin and regular_step:
        log.info(f"[ADMIN_FLOW] Step aktif: {regular_step} oleh {user_id}")

        try:
            match regular_step:
                case "awaiting_admin_id_for_add":
                    await handle_regular_step(client, message, admin_state)

                case "awaiting_admin_id_for_remove":
                    await handle_admin_remove_step(client, message, admin_state)

                case "awaiting_admin_id_for_update":
                    await handle_admin_update_step(client, message, admin_state)

                case "awaiting_source_code" | "awaiting_source_label":
                    await handle_add_source_step(client, message, admin_state)

                case _:
                    log.warning(f"[ADMIN_FLOW] Step tidak dikenali: {regular_step}")
                    await message.reply_text(
                        "⚠️ Langkah tidak dikenali. Silakan ulangi."
                    )
                    cancel_all_states(user_id, source_bot=vip_state.source_bot)
                    await send_dashboard(source=message, is_callback=False)

            return True

        except Exception as e:
            log.error(
                f"❌ [ADMIN_FLOW] Error pada step {regular_step}: {e}", exc_info=True
            )
            await message.reply_text("⚠️ Terjadi kesalahan saat memproses admin.")
            cancel_all_states(user_id, source_bot=vip_state.source_bot)
            await send_dashboard(source=message, is_callback=False)
            return True

    return None
