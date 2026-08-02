# common.utils.fsm_helpers.py

from pyrogram.errors import QueryIdInvalid
from pyrogram.types import CallbackQuery, Message

from apps.drac1n_bot.ui.dashboard import send_dashboard
from shared.utils.callback_helpers import safe_answer, safe_edit_text
from shared.utils.vip_state_manager import VipStateManager
from configs.logging_setup import log


async def validate_step(
    user_id: int, actual_step: str, expected_step: str, source, *, is_callback: bool
) -> bool:
    if actual_step != expected_step:
        log.warning(
            f"[FSM MISMATCH] ❌ expected '{expected_step}', got '{actual_step}' — user_id={user_id}"
        )

        if hasattr(source, "clear") and callable(source.clear):
            source.clear()

        if is_callback:
            # ✅ pakai safe_edit_text supaya tidak error MESSAGE_NOT_MODIFIED
            await safe_edit_text(
                source.message,
                "⚠️ Proses sebelumnya dibatalkan karena urutan tidak sesuai.",
            )
        else:
            await source.reply_text(
                "⚠️ Proses sebelumnya dibatalkan karena urutan tidak sesuai."
            )

        await send_dashboard(source=source, is_callback=is_callback)
        return False

    return True


async def validate_step_from_message(
    message: Message,
    state: VipStateManager,
    expected_step: str,
    fsm_type: str = "vip_add_step",
) -> bool:
    step = _get_step_by_type(state, fsm_type)
    return await validate_step(
        message.from_user.id, step, expected_step, message, is_callback=False
    )


async def validate_step_from_callback(
    callback: CallbackQuery,
    state: VipStateManager,
    expected_step: str,
    fsm_type: str = "vip_add_step",
) -> bool:
    step = _get_step_by_type(state, fsm_type)
    return await validate_step(
        callback.from_user.id, step, expected_step, callback, is_callback=True
    )


async def validate_no_conflict(
    user_id: int,
    state: VipStateManager,
    source,
    *,
    force_clear: bool = True,
    reply_message: str = "⚠️ Anda sedang dalam proses VIP lain. Proses dibatalkan.",
) -> bool:
    """
    Mengecek apakah user sedang dalam proses FSM lain.
    Jika iya, maka state dibatalkan dan dashboard ditampilkan kembali.
    """
    if state.has_conflict():
        log.warning(f"[FSM_CONFLICT] FSM aktif saat masuk: user_id={user_id}")
        if force_clear:
            state.clear()

        try:
            # Jika Message
            if hasattr(source, "reply_text") and callable(source.reply_text):
                await source.reply_text(reply_message)
                await send_dashboard(source=source, is_callback=False)

            # Jika CallbackQuery
            elif (
                hasattr(source, "message")
                and source.message
                and hasattr(source.message, "edit_text")
                and callable(source.message.edit_text)
            ):
                await source.message.edit_text(reply_message)
                try:
                    await source.answer("⚠️ Proses lama dibatalkan")
                except QueryIdInvalid:
                    log.warning(
                        "[FSM_CONFLICT] ⚠️ Query ID invalid saat answer() callback."
                    )
                await send_dashboard(source=source, is_callback=True)

            else:
                log.warning(
                    f"[FSM_CONFLICT] Tidak bisa mengirim feedback ke user_id={user_id}"
                )

        except Exception as e:
            log.error(
                f"[FSM_CONFLICT] ❌ Error saat respon konflik FSM: {e}", exc_info=True
            )

        return False

    return True


async def validate_vip_delete_step_from_callback(
    callback: CallbackQuery,
    state: VipStateManager,
    expected_step: str,
) -> bool:
    return await validate_step_from_callback(
        callback, state, expected_step, fsm_type="vip_delete_step"
    )


def _get_step_by_type(state: VipStateManager, fsm_type: str) -> str | None:
    """
    Helper untuk mengambil nilai step FSM berdasarkan tipe FSM yang sedang aktif di state.

    Args:
        state (VipStateManager): instance state FSM
        fsm_type (str): jenis FSM, misal 'vip_add_step', 'vip_extend_step', dll.

    Returns:
        str | None: nama langkah FSM yang sedang aktif atau None jika tidak ada

    Raises:
        ValueError: jika tipe FSM tidak dikenali
    """
    if fsm_type == "vip_add_step":
        return state.get_vip_add_step()
    elif fsm_type == "vip_extend_step":
        return state.get_vip_extend_step()
    elif fsm_type == "vip_delete_step":
        return state.get_vip_delete_step()
    elif fsm_type == "vip_reset_step":
        return state.get_vip_reset_step()
    else:
        raise ValueError(f"FSM type tidak dikenali: {fsm_type}")
