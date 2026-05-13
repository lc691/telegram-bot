# Refactor lengkap untuk handler extend VIP

import re

from pyrogram import Client
from pyrogram.enums import ParseMode
from pyrogram.types import CallbackQuery

from bots.dramaglow_bot.handlers.vip.extend_vip.vip_build_user_extend import (
    PER_PAGE,
    build_user_extend_markup,
)
from bots.dramaglow_bot.keyboard.vip_tools import (
    generate_confirm_buttons,
    generate_vip_package_buttons,
)
from common.bot_utils import get_clean_bot_key
from common.utils.callback_helpers import safe_answer, safe_edit_text
from common.utils.escape_markdown import escape_md
from common.utils.fsm_helpers import (
    validate_no_conflict,
    validate_step_from_callback,
)
from common.utils.get_user import safe_get_user
from common.utils.vip_state_manager import VipStateManager
from configs.logging_setup import log
from db.vip_users.vip_extend import extend_or_activate_vip
from db.vip_users.vip_status import get_all_active_vip_users, get_vip_status

# =================== Start =====================


async def vip_extend_start(client: Client, callback: CallbackQuery):
    admin_id = callback.from_user.id
    bot_name = getattr(client, "name", "dramaglow_bot")
    source_bot = get_clean_bot_key(bot_name)

    log.info(
        f"[VIP_EXTEND_START] 🚀 Dimulai oleh admin_id={admin_id} di bot={bot_name} (source_bot={source_bot})"
    )

    await safe_answer(callback, "⏳ Memuat data...")

    state = VipStateManager(admin_id, source_bot=source_bot)

    # Cek apakah admin sedang proses FSM lain
    if not await validate_no_conflict(admin_id, state, callback):
        return

    try:
        # Bersihkan state lama
        state.clear()

        # Siapkan FSM baru
        offset = 0
        state.set_temp("vip_extend_offset", offset)
        state.set_temp("source_bot", source_bot)
        state.set_vip_extend_step("vip_extend:waiting_user_selection")

        # ✅ Ambil user VIP aktif
        users = get_all_active_vip_users(
            limit=PER_PAGE, offset=offset, source_bot=source_bot
        )

        if not users:
            await safe_edit_text(
                callback.message, "🚫 Tidak ada user VIP aktif saat ini."
            )
            return

        markup = build_user_extend_markup(users, offset, source_bot)

        await safe_edit_text(
            callback.message,
            "📋 Silakan pilih user yang ingin diperpanjang VIP-nya:",
            reply_markup=markup,
            parse_mode=ParseMode.HTML,
        )

    except Exception as e:
        log.error(
            f"[VIP_EXTEND_START] ❌ Gagal untuk admin_id={admin_id} bot={bot_name}: {e}",
            exc_info=True,
        )
        await safe_edit_text(callback.message, "❌ Gagal memuat daftar user VIP.")


# =================== Pilih User =====================


async def handle_vip_extend_user_selection(
    client: Client, callback: CallbackQuery, state: VipStateManager
):
    admin_id = callback.from_user.id

    if not await validate_step_from_callback(
        callback, state, "vip_extend:waiting_user_selection", "vip_extend_step"
    ):
        return

    try:
        _, user_id_str = callback.data.split(":")
        vip_user_id = int(user_id_str)
    except Exception:
        await safe_answer(callback, "❌ Format callback tidak valid.", show_alert=True)
        state.clear()
        return

    try:
        # ✅ Ambil source_bot dari state
        source_bot = state.get_temp("source_bot") or client.name

        user_info = await client.get_users(vip_user_id)
        username = f"@{user_info.username}" if user_info.username else "-"
        first_name = user_info.first_name or "-"

        # ✅ Ambil paket lama
        vip_info = get_vip_status(vip_user_id, source_bot)
        paket_lama = vip_info["paket"]
        expired_lama = vip_info["expired_str"]

    except Exception as tg_err:
        log.warning(
            f"[VIP_EXTEND] ⚠️ Gagal ambil user_info user_id={vip_user_id}: {tg_err}"
        )
        username, first_name = "-", "-"
        paket_lama, expired_lama = "-", "-"

    state.set_temp("vip_user_id", vip_user_id)
    state.set_vip_extend_step("vip_extend:waiting_package")

    markup = generate_vip_package_buttons("vip_extend")

    text = (
        f"📦 Pilih paket VIP untuk user <code>{vip_user_id}</code>:\n\n"
        f"🔤 Username: {username}\n"
        f"📛 First Name: {first_name}\n"
        f"🆔 User ID: <code>{vip_user_id}</code>\n\n"
        f"🗂 Paket Aktif: {paket_lama}\n"
        f"⏳ Expired: {expired_lama}"
    )
    await safe_edit_text(
        callback.message,
        text,
        reply_markup=markup,
        parse_mode=ParseMode.HTML,
    )


# =================== Pilih Paket =====================

VALID_PAKETS = {"1hari", "3hari", "7hari", "15hari", "30hari", "permanen"}


async def handle_vip_package_selection(
    client: Client, callback: CallbackQuery, state: VipStateManager
):
    admin_id = callback.from_user.id
    data = callback.data

    if data.startswith("vip_extend_"):
        paket = data.removeprefix("vip_extend_")
        mode = "extend"
    else:
        await safe_answer(callback, "❌ Callback tidak valid.", show_alert=True)
        return

    if paket not in VALID_PAKETS:
        await safe_answer(callback, "❌ Paket tidak valid.", show_alert=True)
        return

    if not await validate_step_from_callback(
        callback, state, "vip_extend:waiting_package", "vip_extend_step"
    ):
        return

    state.set_temp("paket", paket)
    state.set_temp("mode", mode)
    state.set_step("vip_extend_step", "vip_extend:waiting_confirmation")

    await safe_edit_text(
        callback.message,
        f"⚠️ Konfirmasi perpanjangan VIP dengan paket: <b>{escape_md(paket)}<b>?",
        reply_markup=generate_confirm_buttons(),
        parse_mode=ParseMode.HTML,
    )


# =================== Konfirmasi =====================


async def handle_vip_extend_confirmation(
    client: Client, callback: CallbackQuery, state: VipStateManager
):
    admin_id = callback.from_user.id

    if not await validate_step_from_callback(
        callback, state, "vip_extend:waiting_confirmation", "vip_extend_step"
    ):
        return

    vip_user_id = state.get_temp("vip_user_id")
    paket = state.get_temp("paket")
    source_bot = state.get_temp("source_bot") or client.name

    if not vip_user_id or not paket:
        await safe_edit_text(callback.message, "❌ Data tidak lengkap.")
        return

    result = extend_or_activate_vip(
        user_id=int(vip_user_id),
        paket=paket,
        admin_id=admin_id,
        source_bot=source_bot,
        keterangan="Perpanjangan oleh admin",
    )

    if not result.get("success"):
        await safe_answer(callback, "❌ Gagal memperpanjang VIP.", show_alert=True)
        return

    try:
        user = await safe_get_user(client, int(vip_user_id))
        admin = await safe_get_user(client, admin_id)
    except:
        user = admin = None

    # ✅ Data hasil extend
    is_extend = result.get("is_extend", False)
    duration = result.get("duration", "-")
    expired_new = result.get("expired_at", "-")
    expired_old = result.get("old_expired", "-")

    user_str = (
        f"{escape_md(user.first_name)}"
        f" ({'@' + user.username if user and user.username else '-'})"
        if user
        else "-"
    )
    admin_str = f"{escape_md(admin.first_name)}" if admin else "-"

    # ✅ Build message konsisten "Perpanjangan"
    msg = (
        f"✅ <b>VIP Diperpanjang</b>\n\n"
        f"👤 {user_str}\n"
        f"🆔 User ID: <code>{vip_user_id}</code>\n"
        f"📦 Paket: <code>{escape_md(paket)}</code>\n"
    )

    # hanya tampilkan expired lama jika tersedia
    if expired_old and expired_old != "-":
        msg += f"⏳ Expired Sebelumnya: <code>{escape_md(expired_old)}</code>\n"

    msg += (
        f"➕ Ditambah: <code>{duration} hari</code>\n"
        f"📅 Expired Baru: <code>{escape_md(expired_new)}</code>\n"
        f"🤖 Bot: <code>{source_bot}</code>\n"
        f"👮 Oleh: {admin_str}"
    )

    await safe_edit_text(callback.message, msg, parse_mode=ParseMode.MARKDOWN)
    state.clear()


# =================== Halaman =====================


async def handle_vip_extend_page(
    client: Client, callback: CallbackQuery, state: VipStateManager
):
    try:
        _, offset_str, bot_name = callback.data.split(":")
        offset = int(offset_str)

        if not await validate_step_from_callback(
            callback, state, "vip_extend:waiting_user_selection", "vip_extend_step"
        ):
            return

        state.set_temp("vip_extend_offset", offset)
        state.set_temp("source_bot", bot_name)

        users = get_all_active_vip_users(
            limit=PER_PAGE, offset=offset, bot_name=bot_name
        )
        if not users:
            await safe_answer(callback, "❌ Tidak ada data user VIP.")
            return

        markup = build_user_extend_markup(users, offset, bot_name)

        await safe_edit_text(
            callback.message,
            "📋 Silakan pilih user yang ingin diperpanjang VIP-nya:",
            reply_markup=markup,
            parse_mode=ParseMode.HTML,
        )

    except Exception as e:
        log.error(f"[VIP_EXTEND_PAGE] ❌ {e}", exc_info=True)
        await safe_answer(callback, "❌ Gagal memuat halaman.", show_alert=True)
