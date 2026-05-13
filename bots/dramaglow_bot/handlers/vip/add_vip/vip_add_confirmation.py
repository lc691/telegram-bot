from pyrogram import Client
from pyrogram.types import CallbackQuery

from bots.dramaglow_bot.handlers.vip.add_vip.vip_add_process import (
    process_vip_activation,
)
from common.bot_utils import get_clean_bot_key
from common.messaging.log_proces import (
    is_valid_data,
    log_action_start,
    log_activation_cancelled,
    log_data_incomplete,
    log_invalid_action,
)
from common.utils.callback_helpers import safe_answer, safe_edit_text
from common.utils.fsm_helpers import validate_step_from_callback
from common.utils.vip_state_manager import VipStateManager
from configs.logging_setup import log


async def handle_vip_add_confirmation(
    app: Client, callback: CallbackQuery, state: VipStateManager
):
    admin_id = callback.from_user.id
    action = callback.data

    try:
        # ✅ Rekonstruksi state dengan prefix bot yang benar
        raw_state = state
        source_bot = get_clean_bot_key(raw_state.get_temp("source_bot") or app.name)
        state = VipStateManager(admin_id, source_bot=source_bot)

        # ✅ Validasi FSM step
        if not await validate_step_from_callback(
            callback, state, expected_step="vip_add:waiting_confirmation"
        ):
            log.warning(f"[VIP_CONFIRM] Invalid FSM step for admin_id={admin_id}")
            return

        # ✅ Ambil data dari state FSM
        vip_user_id = state.get_temp("vip_user_id")
        paket = state.get_temp("paket")
        state.set_temp("source_bot", source_bot)

        log_action_start(admin_id, vip_user_id, paket, action)

        if not is_valid_data(vip_user_id, paket):
            await safe_edit_text(
                callback.message, "❌ Data tidak lengkap. Silakan mulai ulang proses."
            )
            log_data_incomplete(admin_id)
            await safe_answer(callback)
            return

        if action not in {"vip_add_confirm_yes", "vip_add_confirm_no"}:
            await safe_edit_text(callback.message, "❌ Aksi tidak dikenali.")
            log_invalid_action(admin_id, action)
            await safe_answer(callback)
            return

        if action == "vip_add_confirm_yes":
            await process_vip_activation(
                app=app,
                callback=callback,
                admin_id=admin_id,
                vip_user_id=int(vip_user_id),
                paket=paket,
                state=state,
            )
        else:
            await handle_cancel(callback, admin_id)

    except Exception as e:
        log.error(
            f"[VIP_CONFIRM] ❌ Exception terjadi untuk admin_id={admin_id}: {e}",
            exc_info=True,
        )
        try:
            await safe_edit_text(
                callback.message, "⚠️ Terjadi kesalahan saat memproses aktivasi VIP."
            )
            await safe_answer(callback)
        except Exception:
            pass

    finally:
        try:
            state.clear()
            log.info(
                f"[VIP_CONFIRM] ✅ State berhasil dibersihkan untuk admin_id={admin_id}"
            )
        except Exception as clear_err:
            log.error(
                f"[VIP_CONFIRM] ❌ Gagal membersihkan state: {clear_err}",
                exc_info=True,
            )


async def handle_cancel(callback: CallbackQuery, admin_id: int):
    await safe_edit_text(callback.message, "🚫 Aktivasi VIP dibatalkan.")
    await safe_answer(callback)
    log_activation_cancelled(admin_id)
