# ============================================
# wd_pending_detail_handler.py
# ============================================

from datetime import datetime, timezone

from pyrogram import Client, filters
from pyrogram.enums import ParseMode

from common.utils.admin_cache import admin_cache
from configs.logging_setup import log
from db.connect import get_db_cursor

from .wd_admin_handler import build_admin_buttons


def is_admin(user_id: int) -> bool:
    return user_id in admin_cache.admin_ids


@Client.on_message(filters.command("wd_pending_detail") & filters.private)
async def wd_pending_detail_handler(client: Client, message):

    admin_id = message.from_user.id

    if not is_admin(admin_id):
        return await message.reply("🚫 Akses ditolak.")

    args = message.text.split()
    if len(args) != 2 or not args[1].isdigit():
        return await message.reply(
            "📌 Format:\n<code>/wd_pending_detail &lt;wd_id&gt;</code>",
            parse_mode=ParseMode.HTML
        )

    wd_id = int(args[1])

    try:
        with get_db_cursor() as (cursor, _):
            cursor.execute("""
                SELECT
                    w.id,
                    w.user_id,
                    w.amount,
                    w.method,
                    w.target,
                    w.status,
                    w.created_at,
                    u.affiliate_balance
                FROM affiliate_withdraw_requests w
                JOIN users u ON u.user_id = w.user_id
                WHERE w.id=%s
                LIMIT 1
            """, (wd_id,))
            row = cursor.fetchone()

        if not row:
            return await message.reply("❌ WD tidak ditemukan.")

        (
            wd_id,
            user_id,
            amount,
            method,
            target,
            status,
            created_at,
            balance
        ) = row

        status_icon = {
            "pending": "⏳",
            "approved": "✅",
            "rejected": "❌"
        }.get(status, "❓")

        age_min = int(
            (datetime.now(timezone.utc) - created_at).total_seconds() / 60
        )

        warn = ""
        if balance < amount:
            warn = "\n⚠️ <b>Saldo user TIDAK cukup!</b>"

        text = (
            f"📄 <b>Withdraw Detail</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"ID: <code>{wd_id}</code>\n"
            f"User: <code>{user_id}</code>\n"
            f"Status: {status_icon} <b>{status.upper()}</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"💰 Amount: Rp {amount:,}\n"
            f"💳 Method: <b>{method.upper()}</b>\n"
            f"🎯 Target: <code>{target}</code>\n"
            f"🕒 Created: {created_at:%d-%m-%Y %H:%M} UTC\n"
            f"⏱ Age: {age_min} menit\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"💼 Current Balance: Rp {balance:,}"
            f"{warn}\n\n"
            f"👉 Aksi tersedia via tombol di bawah."
        )

        reply_markup = build_admin_buttons(wd_id) if status == "pending" else None

        await message.reply(
            text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )

        log.info(f"[WD_DETAIL] admin={admin_id} wd_id={wd_id}")

    except Exception as e:
        log.error(f"[WD_DETAIL] ERROR: {e}", exc_info=True)
        await message.reply("❌ Gagal mengambil detail WD.")
