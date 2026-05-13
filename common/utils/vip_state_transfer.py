from pyrogram import Client
from pyrogram.enums import ParseMode
from pyrogram.types import CallbackQuery

from common.utils.vip_state_manager import VipStateManager
from configs.logging_setup import log


def force_transfer_state(admin_id: int, from_bot: str, to_bot: str) -> bool:
    try:
        source_state = VipStateManager(admin_id, source_bot=from_bot)
        target_state = VipStateManager(admin_id, source_bot=to_bot)

        exported = source_state.export_state()
        if not exported or exported == {}:
            log.warning(
                f"[VIP_STATE_TRANSFER] Tidak ada state yang bisa dipindahkan dari @{from_bot}"
            )
            return False

        # Tandai bot asal untuk audit
        exported["temp"]["source_bot"] = from_bot

        # Simpan ke bot baru
        target_state.import_state(exported)
        log.info(
            f"[VIP_STATE_TRANSFER] State @{from_bot} → @{to_bot} untuk admin_id={admin_id}"
        )
        return True

    except Exception as e:
        log.error(f"[VIP_STATE_TRANSFER] Gagal transfer state: {e}", exc_info=True)
        return False


async def handle_transfer_vip_state(client: Client, callback: CallbackQuery):
    admin_id = callback.from_user.id
    current_bot = client.name

    # Ambil source_bot dari state sekarang
    temp_state = VipStateManager(admin_id)
    source_bot = temp_state.get_temp("source_bot")

    if not source_bot or source_bot == current_bot:
        await callback.answer(
            "❌ Tidak ada state aktif dari bot lain.", show_alert=True
        )
        return

    success = force_transfer_state(admin_id, from_bot=source_bot, to_bot=current_bot)

    if success:
        await callback.message.edit_text(
            f"✅ State berhasil dipindahkan dari <code>@{source_bot}</code> ke bot ini (<code>@{current_bot}</code>).\n"
            f"Silakan lanjutkan proses.",
            parse_mode=ParseMode.HTML,
        )
    else:
        await callback.answer("❌ Gagal memindahkan state.", show_alert=True)
