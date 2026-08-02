from pyrogram import Client
from pyrogram.enums import ParseMode
from pyrogram.errors import MessageNotModified
from pyrogram.types import CallbackQuery

from apps.dramaglow_bot.keyboard.vip_tools import generate_vip_tools_markup
from shared.utils.callback_helpers import safe_answer, safe_edit_text
from shared.utils.fsm_helpers import validate_step_from_callback
from shared.utils.vip_state_manager import VipStateManager
from configs.logging_setup import log
from database.vip_users.vip_deactivate import remove_vip


async def handle_vip_reset_confirmation(
    app: Client, callback: CallbackQuery, state: VipStateManager
):
    """
    Menangani konfirmasi reset VIP user (Ya / Batal).
    """
    admin_id = callback.from_user.id

    if not await validate_step_from_callback(
        callback, state, expected_step="waiting_confirm", fsm_type="vip_reset_step"
    ):
        return

    vip_user_id = state.get_temp("vip_user_id")
    source_bot = state.get_temp("source_bot") or getattr(app, "bot_name", "glow")

    if not vip_user_id:
        await respond_with_incomplete_data(callback, source_bot)
        log_missing_data(admin_id)
        await safely_clear_state(state, admin_id)
        return

    action = callback.data
    if action == "vip_reset_confirm_yes":
        await process_vip_reset(callback, vip_user_id, source_bot)
    else:
        await process_vip_reset_cancelled(callback, admin_id, source_bot)

    await safely_clear_state(state, admin_id)


# ────────────────────────── Helper Functions ──────────────────────────


async def respond_with_incomplete_data(callback: CallbackQuery, source_bot: str):
    markup = generate_vip_tools_markup(source_bot)
    await safe_edit_text(
        callback.message,
        "❌ Data tidak lengkap. Silakan mulai ulang.",
        reply_markup=markup,
        parse_mode=ParseMode.HTML,
    )


def log_missing_data(user_id: int):
    log.warning(f"[VIP RESET] ❗ Data kosong untuk admin_id={user_id}")


async def process_vip_reset(callback: CallbackQuery, vip_user_id: str, source_bot: str):
    """
    Proses reset VIP berdasarkan ID.
    """
    try:
        result = remove_vip(int(vip_user_id), source_bot=source_bot)
        if result.get("success"):
            reset_message = f"✅ VIP untuk user `{vip_user_id}` berhasil direset."
            log_msg = "[VIP RESET] ✅ Sukses"
        else:
            reason = result.get("reason", "-")
            reset_message = f"❌ Gagal reset VIP. Alasan: `{reason}`"
            log_msg = "[VIP RESET] ⚠️ Gagal"

        markup = generate_vip_tools_markup(source_bot)
        await safe_edit_text(
            callback.message,
            f"{reset_message}\n\n🌟 <b>VIP Tools - {source_bot.capitalize()}<b>",
            reply_markup=markup,
            parse_mode=ParseMode.HTML,
        )

        log.info(f"{log_msg} | user_id={vip_user_id} | bot={source_bot}")

    except Exception as e:
        log.error(
            f"[VIP RESET] ❌ Error saat reset user_id={vip_user_id} | bot={source_bot}: {e}",
            exc_info=True,
        )
        await safe_edit_text(
            callback.message,
            "❌ Terjadi kesalahan saat melakukan reset VIP.",
            parse_mode=ParseMode.HTML,
        )


async def process_vip_reset_cancelled(
    callback: CallbackQuery, admin_id: int, source_bot: str
):
    """
    Proses pembatalan reset VIP.
    """
    try:
        markup = generate_vip_tools_markup(source_bot)
        await safe_edit_text(
            callback.message,
            "🚫 Reset VIP dibatalkan.\n\n🌟 <b>VIP Tools - {source_bot.capitalize()}</b>",
            reply_markup=markup,
            parse_mode=ParseMode.HTML,
        )
    except MessageNotModified:
        await safe_answer(callback, "ℹ️ Tidak ada perubahan.")
    except Exception as e:
        log.error(f"[VIP RESET] ❌ Gagal kembali ke menu: {e}", exc_info=True)

    log.info(f"[VIP RESET] 🚫 Admin {admin_id} membatalkan reset")


async def safely_clear_state(state: VipStateManager, user_id: int):
    try:
        state.clear()
        log.info(f"[VIP RESET] 🔄 State dibersihkan untuk user_id={user_id}")
    except Exception as e:
        log.error(
            f"[VIP RESET] ❌ Gagal hapus state user_id={user_id}: {e}", exc_info=True
        )
