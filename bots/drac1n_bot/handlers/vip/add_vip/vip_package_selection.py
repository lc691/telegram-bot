from pyrogram import Client
from pyrogram.enums import ParseMode
from pyrogram.types import CallbackQuery

from bots.drac1n_bot.keyboard.vip_tools import generate_confirm_buttons
from common.utils.callback_helpers import safe_answer
from common.utils.escape_markdown import escape_md
from common.utils.fsm_helpers import validate_step_from_callback
from common.utils.vip_state_manager import VipStateManager
from configs.logging_setup import log

VALID_PAKETS = {"1hari", "3hari", "7hari", "15hari", "30hari", "permanen"}


async def handle_vip_package_selection(client: Client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    data = callback_query.data
    bot_name = getattr(client, "bot_name", client.name)

    if data.startswith("vip_add_"):
        mode = "add"
        paket = data.removeprefix("vip_add_")
    elif data.startswith("vip_extend_"):
        mode = "extend"
        paket = data.removeprefix("vip_extend_")
    else:
        await safe_answer(
            callback_query, "❌ Callback tidak dikenali.", show_alert=True
        )
        return

    log.info(
        "[VIP_PACKAGE_SELECTION] user_id=%s memilih paket=%s mode=%s",
        user_id,
        paket,
        mode,
    )

    if not is_valid_paket(paket):
        await notify_invalid_paket(callback_query, paket)
        return

    state = VipStateManager(user_id, source_bot=bot_name)
    expected_step = f"vip_{mode}:waiting_package"
    set_step_func = (
        state.set_vip_add_step if mode == "add" else state.set_vip_extend_step
    )

    # ✅ Validasi FSM harus pada step yang sesuai
    if not await validate_step_from_callback(
        callback_query,
        state,
        expected_step=expected_step,
        fsm_type=f"vip_{mode}_step",
    ):
        return

    try:
        state.set_temp("paket", paket)
        state.set_temp("mode", mode)
        set_step_func(f"vip_{mode}:waiting_confirmation")

        await send_confirmation(callback_query, escape_md(paket), mode)

    except Exception as e:
        log.error(
            "[VIP_PACKAGE_SELECTION] ❌ Error user_id=%s: %s", user_id, e, exc_info=True
        )
        await safe_answer(
            callback_query, "❌ Terjadi kesalahan saat memilih paket.", show_alert=True
        )


# ========== Helper Functions ==========


def is_valid_paket(paket: str) -> bool:
    return paket in VALID_PAKETS


async def notify_invalid_paket(callback_query: CallbackQuery, paket: str):
    log.warning("[VIP_PACKAGE_SELECTION] ⚠️ Paket tidak valid: %s", paket)
    await safe_answer(callback_query, "❌ Paket tidak valid.", show_alert=True)


async def send_confirmation(callback_query: CallbackQuery, paket: str, mode: str):
    await safe_answer(callback_query)  # Hapus loading tombol callback

    label = "perpanjangan" if mode == "extend" else "aktivasi"
    try:
        await callback_query.message.edit_text(
            f"⚠️ Konfirmasi {label} VIP dengan paket: <b>{paket}</b>?",
            reply_markup=generate_confirm_buttons(mode=f"vip_{mode}"),
            parse_mode=ParseMode.HTML,
        )
    except Exception as e:
        log.error(
            "[VIP_PACKAGE_SELECTION] ❌ Gagal edit pesan konfirmasi: %s",
            e,
            exc_info=True,
        )
