from pyrogram import Client
from pyrogram.enums import ParseMode
from pyrogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from shared.utils.callback_helpers import safe_answer
from shared.utils.fsm_helpers import validate_no_conflict
from shared.utils.vip_state_manager import VipStateManager
from configs.logging_setup import log
from database.vip_users.vip_status import get_all_active_vip_users, get_vip_status


async def vip_reset_start(client: Client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    state = VipStateManager(user_id)

    source_bot = state.get_temp("source_bot") or "glow"
    state.set_temp("source_bot", source_bot)

    # ✅ FSM Guard
    if not await validate_no_conflict(user_id, state, callback_query):
        return

    try:
        vip_list = get_all_active_vip_users(limit=30, source_bot=source_bot)
        if not vip_list:
            await callback_query.message.edit_text(
                f"⚠️ Tidak ada user VIP aktif di bot <code>{source_bot}</code>.",
                parse_mode=ParseMode.HTML,
            )
            await safe_answer(callback_query)
            return

        # Generate tombol pilihan VIP
        buttons = []
        for vip in vip_list:
            label = (
                f"`{vip['user_id']}` | "
                f"{vip['username'] or '-'} | "
                f"{vip['paket'] or '-'} | "
                f"s.d {vip['end_date'].strftime('%d %b %Y %H:%M') if vip['end_date'] else '-'}"
            )
            buttons.append(
                [
                    InlineKeyboardButton(
                        text=label,
                        callback_data=f"vip_reset_select_{vip['user_id']}",
                    )
                ]
            )

        # Tombol batal
        buttons.append(
            [InlineKeyboardButton("❌ Batal", callback_data=f"vip_tools:{source_bot}")]
        )

        await callback_query.message.edit_text(
            f"🔄 Pilih user yang ingin direset VIP-nya (Bot: <code>{source_bot}</code>):",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(buttons),
        )
        await safe_answer(callback_query)

    except Exception as e:
        log.error(f"[VIP_RESET_START] Gagal tampilkan list VIP: {e}", exc_info=True)
        await callback_query.answer(
            "❌ Gagal menampilkan daftar user VIP.", show_alert=True
        )


async def handle_vip_reset_selection(client: Client, callback_query: CallbackQuery):
    """
    Menangani pemilihan user VIP yang ingin direset.
    """
    admin_id = callback_query.from_user.id
    state = VipStateManager(admin_id)

    try:
        data = callback_query.data
        user_id_str = data.replace("vip_reset_select_", "")
        vip_user_id = int(user_id_str)

        source_bot = state.get_temp("source_bot") or "glow"
        state.set_temp("vip_user_id", str(vip_user_id))
        state.set_temp("source_bot", source_bot)
        state.set_vip_reset_step("waiting_confirm")

        status = get_vip_status(vip_user_id, source_bot=source_bot)

        if not status or not status.get("is_vip"):
            await callback_query.message.edit_text(
                f"⚠️ User <code>{vip_user_id}</code> tidak memiliki status VIP aktif.",
                parse_mode=ParseMode.HTML,
            )
            await safe_answer(callback_query)
            return

        # Informasi status VIP
        end_date_str = (
            status["end_date"].strftime("%d %b %Y %H:%M") if status["end_date"] else "-"
        )
        paket = status.get("paket") or "-"

        # Konfirmasi
        await callback_query.message.edit_text(
            (
                f"⚠️ <b>Yakin ingin mereset VIP user</b> "
                f"<code>{vip_user_id}</code>?\n\n"
                f"📦 <b>Paket:</b> <code>{paket}</code>\n"
                f"📅 <b>Aktif s/d:</b> <code>{end_date_str}</code>\n"
                f"🤖 <b>Bot:</b> <code>{source_bot}</code>"
            ),
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "✅ Ya", callback_data="vip_reset_confirm_yes"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "❌ Batal", callback_data=f"vip_tools:{source_bot}"
                        )
                    ],
                ]
            ),
        )
        await safe_answer(callback_query)

    except Exception as e:
        log.error(f"[VIP_RESET_SELECT] Gagal handle selection: {e}", exc_info=True)
        await callback_query.answer("❌ Gagal memproses pilihan user.", show_alert=True)
