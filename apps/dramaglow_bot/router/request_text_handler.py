import asyncio
import re

from pyrogram import Client
from pyrogram.enums import ParseMode
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from shared.texts.forbiden_text import contains_forbidden_content
from shared.utils.callback_helpers import safe_reply
from shared.utils.request_state_manager import UserRequestStateManager
from configs.logging_setup import log

from ..repository.request_log_repository import save_request_log
from ..delivery.telegram.user.file.services.file_service import get_post_by_main_title


# =========================
# 🔁 Fungsi Utama Handler
# =========================
async def handle_request_text(client: Client, message: Message) -> bool:
    user_id = message.from_user.id

    if not message.text:
        return False

    raw_text = message.text.strip()

    # 🔒 Filter konten SARA
    if contains_forbidden_content(raw_text):
        log.warning(f"🚫 Konten terlarang dari user {user_id}: '{raw_text}'")
        return True  # Diam-diam abaikan

    state = UserRequestStateManager(user_id)

    if state.get_step() != "input_title":
        return False

    formatted_title = " ".join(raw_text.split()).title()

    data = state.get_data()
    source_code = data.get("source_code")
    preset_title = data.get("title")

    title_to_use = preset_title or formatted_title

    if not title_to_use:
        await safe_reply(message, "⚠️ Judul tidak boleh kosong.")
        return True

    try:
        db_post = await asyncio.to_thread(get_post_by_main_title, title_to_use)

        if db_post and db_post.get("message_id"):
            channel_username = "dramaglow"
            post_link = f"https://t.me/{channel_username}/{db_post['message_id']}"
            await safe_reply(
                message,
                (
                    "✅ Drama dengan judul serupa sudah tersedia!\n\n"
                    f"📺 Link: {post_link}"
                ),
            )
            return True

        user = message.from_user
        username = user.username or "-"
        first_name = user.first_name or "-"
        username_text = (
            f"🔗 <b>Username:</b> @{username}"
            if username != "-"
            else "🔗 <b>Username:</b> <i>(tidak ada)</i>"
        )

        admin_msg = (
            "🌸 <b>Permintaan Drama Baru!</b> 🌸\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            f"🎬 <b>Judul Drama:</b> <i>{title_to_use}</i>\n"
            f"📺 <b>Dari Platform:</b> <code>{source_code}</code>\n\n"
            f"🧕 <b>Pengirim:</b> {first_name}\n"
            f"{username_text}\n"
            f"🆔 <b>ID:</b> <code>{user_id}</code>\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            "💌 <i>Cinta pengguna drama ini butuh perhatian admin~</i>"
        )

        admin_message = await client.send_message(
            chat_id="@requestdcstv",
            text=admin_msg,
            parse_mode=ParseMode.HTML,
        )

        await safe_reply(
            message,
            (
                "✅ <b>Request kamu berhasil dikirim ke admin!</b>\n\n"
                f"🎯 <b>Source:</b> <code>{source_code}</code>\n"
                f"🎬 <b>Judul:</b> <code>{title_to_use}</code>\n\n"
                "⏳ Mohon tunggu, admin akan meninjau permintaanmu.\n"
                "Kamu bisa cek status atau kirim request lain nanti. 🙌"
            ),
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "📡 Cek Channel Request", url="https://t.me/requestdcstv"
                        )
                    ]
                ]
            ),
            parse_mode=ParseMode.HTML,
        )

        log.info(
            f"✅ Request '{title_to_use}' dari user {user_id} berhasil dikirim ke admin."
        )

    except Exception as e:
        log.exception(f"❌ Gagal memproses request text user {user_id}: {e}")
        await safe_reply(
            message,
            "⚠️ Terjadi kesalahan saat memproses permintaanmu. Mohon coba lagi nanti.",
        )
    finally:
        save_request_log(
            user_id,
            message.from_user.username,
            message.from_user.first_name,
            source_code,
            title_to_use,
        )
        state.clear_all()

    return True
