import re

from pyrogram import Client
from pyrogram.enums import ChatAction, ParseMode
from pyrogram.types import Message

from bots.bots_registry import get_bot
from bots.drac1n_bot.keyboard.vip_tools import generate_vip_package_buttons
from common.utils.callback_helpers import safe_reply
from common.utils.escape_markdown import escape_md
from common.utils.fsm_helpers import validate_step_from_message
from common.utils.vip_state_manager import VipStateManager
from configs.logging_setup import log
from db.vip_users.vip_status import check_vip_status


async def handle_ask_user_id(
    client: Client, message: Message, user_input: str, state: VipStateManager
):
    user_id = message.from_user.id
    user_input = user_input.strip()

    # ✅ Validasi step FSM (konsisten dengan step yang diset sebelumnya)
    if not await validate_step_from_message(
        message, state, expected_step="vip_add:ask_user_id", fsm_type="vip_add_step"
    ):
        return

    # ✅ Validasi format user_id
    if not re.fullmatch(r"\d{4,15}", user_input):
        return await safe_reply(message, "❌ User ID harus berupa angka 4–15 digit.")

    target_id = int(user_input)
    source_bot = state.get_temp("source_bot") or client.name

    # Cegah duplikasi input jika sudah lanjut
    if state.get_vip_add_step() == "vip_add:waiting_package":
        log.info(f"[VIP_ADD] ⏭️ Admin {user_id} sudah di tahap paket.")
        return await safe_reply(message, "⚠️ Proses sudah di tahap pemilihan paket.")

    await message.reply_chat_action(ChatAction.TYPING)

    # ✅ Cek status VIP target user
    status = check_vip_status(target_id, source_bot=source_bot)
    if status is None or status.get("not_found"):
        return await safe_reply(
            message,
            "❌ User belum memulai bot atau tidak ditemukan.\n"
            "Pastikan user telah memulai bot ini terlebih dahulu.",
        )

    # ✅ Ambil info user
    try:
        user_info = await client.get_users(target_id)
        username = f"@{user_info.username}" if user_info.username else "-"
        first_name = user_info.first_name or "-"
    except Exception as tg_err:
        log.warning(f"[VIP_ADD] ⚠️ Gagal ambil user_info user_id={target_id}: {tg_err}")
        username, first_name = "-", "-"

    username = escape_md(username)
    first_name = escape_md(first_name)

    # ✅ Simpan temp data FSM
    state.set_temp("vip_user_id", str(target_id))
    state.set_temp("source_bot", source_bot)
    state.set_temp("is_vip", status.get("is_vip", False))
    state.set_temp("expired_at", status.get("expired_at", "tidak diketahui"))
    state.set_vip_add_step("vip_add:waiting_package")

    reply_text = (
        f"🔤 Username: {username}\n"
        f"📛 First Name: {first_name}\n"
        f"🆔 User ID: <code>{target_id}</code>\n"
        f"🤖 Bot: <code>{source_bot}</code>\n\n"
        f"🔁 Status: {'SUDAH VIP' if status.get('is_vip') else 'BELUM VIP'}\n"
        f"🛑 Expired: <code>{status.get('expired_at', '-')}</code>\n\n"
        f"📦 Silakan pilih paket untuk {'memperpanjang' if status.get('is_vip') else 'aktivasi'} VIP:"
    )

    buttons = generate_vip_package_buttons()
    if not buttons.inline_keyboard:
        return await safe_reply(message, "⚠️ Tidak ada paket VIP tersedia saat ini.")

    # ✅ Kirim pesan via bot FSM
    true_bot = get_bot(source_bot) or client
    try:
        await true_bot.send_message(
            chat_id=user_id,
            text=reply_text,
            parse_mode=ParseMode.HTML,
            reply_markup=buttons,
        )
    except Exception as e:
        log.error(f"[VIP_ADD] ❌ Gagal kirim pilihan paket VIP: {e}", exc_info=True)
        await safe_reply(
            message,
            "❌ Gagal mengirim pilihan paket VIP. Silakan coba lagi.",
        )
