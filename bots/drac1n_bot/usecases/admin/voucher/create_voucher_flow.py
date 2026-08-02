from datetime import datetime
from pytz import timezone
from pyrogram import Client
from pyrogram.types import Message

from config import POSTING_TEST
from configs.logging_setup import log

from .voucher_parser import parse_voucher_command
from ....repository.voucer_repository import generate_bulk_vouchers
from ....presenters.admin.voucher.voucher_keyboard import build_voucher_keyboard
from .voucher_text_builder import build_voucher_text

TZ_WIB = timezone("Asia/Jakarta")


async def handle_voucher_command(client: Client, message: Message):
    now = datetime.now(TZ_WIB).strftime("%Y-%m-%d %H:%M:%S")
    admin = message.from_user
    admin_username = admin.username or f"user{admin.id}"

    parsed = parse_voucher_command(message.text)
    if not parsed:
        await message.reply(
            "❗ Format salah.\n\n"
            "<code>/voucher &lt;jml&gt; &lt;hari&gt; 'judul' 'konten'</code>",
            parse_mode="html",
        )
        return

    try:
        vouchers, batch_id = generate_bulk_vouchers(
            parsed.amount,
            parsed.duration_days,
            created_by=admin_username,
        )

        text = build_voucher_text(
            title=parsed.title,
            content=parsed.content,
            vouchers=vouchers,
            amount=parsed.amount,
            duration=parsed.duration_days,
        )

        await client.send_message(
            chat_id=POSTING_TEST,
            text=text,
            parse_mode="html",
            reply_markup=build_voucher_keyboard(),
            disable_web_page_preview=True,
        )

        await message.reply(
            f"✅ <b>{parsed.amount} voucher terkirim</b>\n"
            f"🆔 Batch: <code>{batch_id}</code>\n"
            f"🕒 {now} WIB",
            parse_mode="html",
        )

        log.info(
            "[%s] [VOUCHER] admin=%s batch=%s amount=%s",
            now,
            admin_username,
            batch_id,
            parsed.amount,
        )

    except Exception:
        log.exception("[VOUCHER] ERROR admin=%s", admin_username)
        await message.reply("❌ Gagal membuat voucher.")
