from pyrogram import Client
from pyrogram.enums import ParseMode
from pyrogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from apps.dramaglow_bot.keyboard.vip_tools import generate_delete_confirm_buttons
from shared.bot_utils import get_clean_bot_key
from shared.utils.callback_helpers import safe_answer, safe_edit_text
from shared.utils.escape_markdown import escape_md
from shared.utils.fsm_helpers import (
    validate_vip_delete_step_from_callback,
)
from shared.utils.vip_state_manager import VipStateManager
from configs.logging_setup import log
from database.vip_users.vip_deactivate import remove_vip
from database.vip_users.vip_status import check_vip_status, get_all_active_vip_users


async def vip_delete_start(client: Client, callback_query: CallbackQuery):
    admin_id = callback_query.from_user.id
    bot_name = getattr(client, "name", "dramaglow_bot")
    source_bot = get_clean_bot_key(bot_name)

    log.info(
        f"[VIP_DELETE_START] 🚀 Dimulai oleh admin_id={admin_id} di bot={bot_name} (source_bot={source_bot})"
    )

    state = VipStateManager(admin_id, source_bot=bot_name)

    # Bersihkan semua state sebelumnya
    state.clear()

    # Set sumber bot
    state.set_temp("source_bot", bot_name)

    # Setelah aman, set FSM step
    state.set_vip_delete_step("waiting_user_selection")

    # ✅ Panggil query pakai source_bot
    vip_users = get_all_active_vip_users(limit=20, source_bot=source_bot)
    if not vip_users:
        await safe_edit_text(
            callback_query.message,
            "🚫 Tidak ada user VIP aktif yang ditemukan.",
        )
        await safe_answer(callback_query)
        return

    # Buat tombol user
    buttons = []
    for user in vip_users:
        username = f"@{user['username']}" if user["username"] else "-"
        user_id = user["user_id"]
        expired_at = user.get("end_date", "—")
        paket = user.get("paket", "-")
        first_name = user.get("first_name", "-")

        if expired_at and expired_at != "—":
            expired_at_str = expired_at.strftime("%d %b %Y %H:%M")
        else:
            expired_at_str = "—"

        label = f"{first_name} ({username}) | {paket} | ⏳ {expired_at_str}"

        buttons.append(
            [
                InlineKeyboardButton(
                    text=label, callback_data=f"vip_delete_select_{user_id}"
                )
            ]
        )

    # Tombol batal
    buttons.append([InlineKeyboardButton("❌ Batal", callback_data="vip_delete_no")])

    text = (
        "👥 <b>Daftar User VIP Aktif<b>\n\n"
        f"✅ Ditemukan {len(vip_users)} user VIP aktif di bot <code>{escape_md(source_bot)}</code>.\n\n"
    )

    if len(vip_users) >= 20:
        text += "⚠️ Ditampilkan maksimal 20 user saja.\n\n"

    text += (
        "Pilih salah satu user di bawah ini untuk menghapus VIP-nya.\n"
        "Atau tekan ❌ <b>Batal</b> jika tidak jadi."
    )

    await safe_edit_text(
        callback_query.message,
        text,
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode=ParseMode.HTML,
    )
    await safe_answer(callback_query)

    log.info(
        "[VIP_DELETE_START] ✅ Menampilkan %s user VIP aktif ke admin_id=%s (bot=%s)",
        len(vip_users),
        admin_id,
        bot_name,
    )


async def handle_vip_delete_selection(client: Client, callback_query: CallbackQuery):
    admin_id = callback_query.from_user.id
    bot_name = getattr(client, "bot_name", client.name)

    state = VipStateManager(admin_id, source_bot=bot_name)

    if not await validate_vip_delete_step_from_callback(
        callback_query, state, expected_step="waiting_user_selection"
    ):
        return

    try:
        _, user_id_str = callback_query.data.split("_select_")
        user_id = int(user_id_str)
    except Exception:
        await safe_answer(
            callback_query, "❌ Format callback tidak valid.", show_alert=True
        )
        state.clear()
        return

    # Ambil detail VIP user
    status = get_all_active_vip_users(user_id, source_bot=bot_name)

    expired = status.get("expired_at") or "—"
    paket = status.get("paket") or "-"
    first_name = status.get("first_name") or "-"
    username = f"@{status.get('username')}" if status.get("username") else "-"

    state.set_temp("vip_user_id", str(user_id))
    state.set_vip_delete_step("waiting_confirmation")

    text = (
        f"⚠️ Yakin ingin menghapus status VIP user berikut?\n\n"
        f"👤 Nama: {escape_md(first_name)}\n"
        f"🔤 Username: {escape_md(username)}\n"
        f"🆔 User ID: <code>{escape_md(str(user_id))}</code>\n"
        f"📦 Paket: <code>{escape_md(paket)}</code>\n"
        f"📅 Expired: <code>{escape_md(str(expired))}</code>"
    )

    await safe_edit_text(
        callback_query.message,
        text,
        parse_mode=ParseMode.HTML,
        reply_markup=generate_delete_confirm_buttons(),
    )
    await safe_answer(callback_query)

    log.info(
        "[VIP_DELETE_SELECT] ✅ Konfirmasi hapus ditampilkan untuk user_id=%s oleh admin_id=%s",
        user_id,
        admin_id,
    )


async def handle_vip_delete_confirmation(client: Client, callback_query: CallbackQuery):
    admin_id = callback_query.from_user.id
    bot_name = getattr(client, "bot_name", client.name)
    source_bot = get_clean_bot_key(bot_name)

    state = VipStateManager(admin_id, source_bot=bot_name)

    if not await validate_vip_delete_step_from_callback(
        callback_query, state, expected_step="waiting_confirmation"
    ):
        return

    action = callback_query.data
    vip_user_id = state.get_temp("vip_user_id")

    if not vip_user_id:
        await safe_edit_text(callback_query.message, "❌ Data tidak lengkap.")
        return

    if action == "vip_delete_confirm_yes":
        result = remove_vip(int(vip_user_id), source_bot=source_bot)
        if result.get("success"):
            status = check_vip_status(int(vip_user_id), source_bot=source_bot)
            first_name = status.get("first_name") or "-"
            username = f"@{status.get('username')}" if status.get("username") else "-"
            await safe_edit_text(
                callback_query.message,
                f"✅ Status VIP user berhasil dihapus:\n\n"
                f"👤 Nama: {escape_md(first_name)}\n"
                f"🔤 Username: {escape_md(username)}\n"
                f"🆔 User ID: <code>{escape_md(str(vip_user_id))}</code>",
                parse_mode=ParseMode.HTML,
            )
            log.info(
                "[VIP_DELETE_CONFIRMATION] ✅ Berhasil hapus VIP user_id=%s (bot=%s) oleh admin_id=%s",
                vip_user_id,
                source_bot,
                admin_id,
            )
        else:
            await safe_edit_text(
                callback_query.message,
                f"❌ Gagal menghapus VIP user <code>{escape_md(str(vip_user_id))}</code>.",
                parse_mode=ParseMode.HTML,
            )
            log.error(
                "[VIP_DELETE_CONFIRMATION] ❌ Gagal menghapus VIP user_id=%s: %s",
                vip_user_id,
                result.get("reason", "-"),
            )
    else:
        await safe_edit_text(
            callback_query.message,
            "🚫 Penghapusan VIP dibatalkan.",
        )
        log.info(
            "[VIP_DELETE_CONFIRMATION] Penghapusan VIP dibatalkan oleh admin_id=%s",
            admin_id,
        )

    state.clear()
