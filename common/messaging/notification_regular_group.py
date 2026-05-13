# =====================[ NOTIF DONASI - KOMENTAR OTOMATIS + AUTO DELETE ]=====================
import asyncio
import html
from datetime import datetime
from typing import Optional
import random

from pyrogram import Client
from pyrogram.enums import ParseMode

from configs.logging_setup import log

AUTO_DELETE_SECONDS = 600
AUTO_COMMENT_TEXT = "https://t.me/tutorialvip1/22"

MAX_TOTAL_LENGTH = 600


async def send_donation_group_announcement(
    app: Client,
    chat_id: int | str,
    username: str,
    paket: str,
    message_text: str,
    note_empty: str,
    email: Optional[str] = None,
    tx_time: Optional[datetime] = None,
    user_id: Optional[int] = None,
):
    """
    Kirim notifikasi donasi ke channel dan hapus otomatis setelah delay.
    """
    try:
        # === 1️⃣ Escape semua input berbasis user ===
        username = html.escape(username)
        paket = html.escape(paket)
        pesan_display = html.escape(message_text or "")
        email = html.escape(email) if email else None
        note_empty = (note_empty) if note_empty else ""

        caption_template = (
            "💖 <b>Terima kasih atas Donasi!</b>\n"
            "━━━━━━━━━━━━━━━━━━━\n\n"
            f"👤 Donatur: <b>{username}</b>\n"
        )

        if user_id:
            caption_template += f"🆔 User ID: <code>{user_id}</code>\n"

        if email and email.lower() != "unknown":
            caption_template += f"📧 Email: <code>{email}</code>\n"

        caption_template += (
            f"💵 Jumlah: <b>{paket}</b>\n"
            f"📝 Pesan: {{pesan}}\n\n"
            f"{note_empty}\n"
            f"⏰ {tx_time.strftime('%d %B %Y %H:%M WIB') if tx_time else ''}\n"
            "━━━━━━━━━━━━━━━━━━━"
        )

        # === 2️⃣ Batasi panjang total caption ===
        base_length = len(caption_template.format(pesan=""))
        remaining = max(0, MAX_TOTAL_LENGTH - base_length)

        if len(pesan_display) > remaining:
            pesan_display = pesan_display[: max(0, remaining - 3)] + "..."

        caption = caption_template.format(pesan=pesan_display)

        # === 3️⃣ Kirim pesan ke CHANNEL ===
        msg = await app.send_message(
            chat_id=chat_id,
            text=caption,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
        )

        log.info(
            f"[DONASI] 📢 Pesan donasi dikirim | chat_id={chat_id} msg_id={msg.id}"
        )

        # === 3️⃣b AUTO COMMENT KE DISKUSI (DELAY RANDOM 1–2s) ===
        try:
            delay = random.uniform(1.0, 2.0)
            await asyncio.sleep(delay)

            await app.send_message(
                chat_id=chat_id,
                text=AUTO_COMMENT_TEXT,
                reply_to_message_id=msg.id,
                disable_web_page_preview=False,
            )

            log.info(
                f"[DONASI][COMMENT] 💬 Auto comment terkirim | reply_to={msg.id} delay={delay:.2f}s"
            )
        except Exception as e:
            log.warning(
                "[DONASI][COMMENT] ⚠️ Gagal kirim auto comment",
                exc_info=e,
            )

        # === 4️⃣ Jadwalkan auto-delete (fire-and-forget) ===
        asyncio.create_task(
            _auto_delete_message(
                app=app,
                chat_id=chat_id,
                message_id=msg.id,
                delay=AUTO_DELETE_SECONDS,
            ),
            name=f"auto_delete_donation_{chat_id}_{msg.id}",
        )

    except Exception as e:
        log.error("[DONASI][FATAL] Gagal kirim notifikasi donasi", exc_info=e)


async def _auto_delete_message(
    app: Client,
    chat_id: int | str,
    message_id: int,
    delay: int,
):
    """Hapus pesan otomatis setelah delay (detik)."""
    try:
        await asyncio.sleep(delay)
        await app.delete_messages(chat_id, message_id)
        log.info(
            f"[DONASI][AUTO_DELETE] 🗑️ Pesan dihapus | chat_id={chat_id} msg_id={message_id}"
        )
    except Exception as e:
        log.warning(
            f"[DONASI][AUTO_DELETE] ⚠️ Gagal hapus pesan | chat_id={chat_id} msg_id={message_id} err={e}"
        )
