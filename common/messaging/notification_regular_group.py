import asyncio
import html
import random
from datetime import datetime
from typing import Optional

from pyrogram import Client
from pyrogram.enums import ParseMode

from configs.logging_setup import log

AUTO_DELETE_SECONDS = 36000
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
    status: str = "success",  # success | failed
    fail_reason: Optional[str] = None,
):
    """
    Kirim notifikasi donasi / gagal VIP.
    """

    try:
        # =========================
        # SAFE INPUT
        # =========================
        username = html.escape(username or "-")
        paket = html.escape(paket or "-")
        pesan_display = html.escape(message_text or "-")
        email = html.escape(email) if email else None
        note_empty = html.escape(note_empty or "")

        tx_display = (
            tx_time.strftime("%d %B %Y %H:%M WIB")
            if tx_time
            else "-"
        )

        # =========================
        # HEADER
        # =========================
        if status == "failed":
            header = "⚠️ <b>TRANSAKSI TIDAK TERVERIFIKASI</b>"
            subtitle = "Donasi tidak dapat diproses menjadi VIP aktif"
        else:
            header = "💖 <b>DONASI BERHASIL DITERIMA</b>"
            subtitle = "Terima kasih atas dukunganmu ❤️"

        # =========================
        # BASE CAPTION
        # =========================
        caption_template = (
            f"{header}\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"📌 {subtitle}\n\n"
            f"👤 Donatur: <b>{username}</b>\n"
            f"💵 Jumlah: <b>{paket}</b>\n"
            f"📝 Pesan: {{pesan}}\n"
            f"⏰ <code>{tx_display}</code>\n"
        )

        if user_id:
            caption_template += (
                f"🆔 User ID: <code>{user_id}</code>\n"
            )

        if email and email.lower() != "unknown":
            caption_template += (
                f"📧 Email: <code>{email}</code>\n"
            )

        # =========================
        # FAILED MODE
        # =========================
        if status == "success":
            reason_text = html.escape(
                fail_reason or
                "Data pembayaran tidak valid / tidak terdeteksi"
            )

            caption_template += (
                "\n"
                "❌ <b>Status:</b> GAGAL MASUK VIP\n\n"
                "📎 <b>Kemungkinan penyebab:</b>\n"
                " ├─ Transaksi <b>Anonymous/Private</b>\n"
                " ├─ Metode <b>pembayaran tidak Valid</b>\n"
                " └─ Data VIP tidak terbaca sistem\n\n"
                f"ℹ️ <b>Detail:</b> <i>{reason_text}</i>\n\n"
                "═══════✦✧✦═══════\n"
                "📌 <b>Solusi:</b>\n"
                " ├─ Pastikan tidak centang Anonymous/Private\n"
                " ├─ Gunakan metode pembayaran yang <b>direkomendasikan</b>\n"
                " └─ 📚 <a href='https://t.me/tutorialvip1/22'>Panduan VIP</a>"
            )

        # =========================
        # SUCCESS MODE
        # =========================
        else:
            if note_empty:
                caption_template += f"\n{note_empty}\n"

        # =========================
        # FOOTER
        # =========================
        caption_template += (
            "\n═══════✦✧✦═══════\n\n"
            "🛡️ <b>Garansi Hanya:</b>\n"
            "<i>Berlaku untuk pembelian paket</i> <b>VIP 15 Hari dan 30 Hari.</b>"
        )

        # =========================
        # LENGTH CONTROL
        # =========================
        base_length = len(caption_template.format(pesan=""))
        remaining = max(0, MAX_TOTAL_LENGTH - base_length)

        if len(pesan_display) > remaining:
            pesan_display = (
                pesan_display[: max(0, remaining - 3)] + "..."
            )

        caption = caption_template.format(
            pesan=pesan_display
        )

        # =========================
        # SEND MESSAGE
        # =========================
        msg = await app.send_message(
            chat_id=chat_id,
            text=caption,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
        )

        log.info(
            f"[DONASI] 📢 Sent | "
            f"chat_id={chat_id} "
            f"msg_id={msg.id} "
            f"status={status}"
        )

        # =========================
        # AUTO COMMENT (SUCCESS ONLY)
        # =========================
        if status == "success":
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
                    f"[DONASI][COMMENT] 💬 Sent | "
                    f"reply_to={msg.id} "
                    f"delay={delay:.2f}s"
                )

            except Exception as e:
                log.warning(
                    "[DONASI][COMMENT] ⚠️ Failed",
                    exc_info=e,
                )

        # =========================
        # AUTO DELETE TASK
        # =========================
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
        log.error(
            "[DONASI][FATAL] Failed sending notification",
            exc_info=e,
        )


async def _auto_delete_message(
    app: Client,
    chat_id: int | str,
    message_id: int,
    delay: int,
):
    try:
        await asyncio.sleep(delay)

        await app.delete_messages(
            chat_id,
            message_id,
        )

        log.info(
            f"[DONASI][AUTO_DELETE] 🗑️ Deleted | "
            f"chat_id={chat_id} "
            f"msg_id={message_id}"
        )

    except Exception as e:
        log.warning(
            f"[DONASI][AUTO_DELETE] ⚠️ Failed delete | "
            f"chat_id={chat_id} "
            f"msg_id={message_id} "
            f"err={e}"
        )