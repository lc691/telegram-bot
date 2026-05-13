# ============================================
# wd_pending_handler.py
# ============================================

from datetime import datetime, timezone

from pyrogram import Client, filters
from pyrogram.enums import ParseMode

from common.utils.admin_cache import admin_cache
from configs.logging_setup import log
from db.connect import get_db_cursor

MAX_SHOW = 10


def is_admin(user_id: int) -> bool:
    return user_id in admin_cache.admin_ids


@Client.on_message(filters.command("wd_pending") & filters.private)
async def wd_pending_handler(client: Client, message):

    admin_id = message.from_user.id

    if not is_admin(admin_id):
        return await message.reply("🚫 Akses ditolak.")

    try:
        with get_db_cursor() as (cursor, _):
            cursor.execute("""
                SELECT id, user_id, amount, method, target, created_at
                FROM affiliate_withdraw_requests
                WHERE status = 'pending'
                ORDER BY created_at ASC
                LIMIT %s
            """, (MAX_SHOW,))
            rows = cursor.fetchall()

        if not rows:
            return await message.reply(
                "✅ <b>Tidak ada withdraw pending.</b>",
                parse_mode=ParseMode.HTML
            )

        text = (
            f"📋 <b>Withdraw Pending</b> (max {MAX_SHOW})\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
        )

        now = datetime.now(timezone.utc)

        for wd_id, user_id, amount, method, target, created_at in rows:
            age_min = int((now - created_at).total_seconds() / 60)
            flag = " ⏰" if age_min > 60 else ""

            text += (
                f"\n🆔 <code>{wd_id}</code>\n"
                f"👤 User: <code>{user_id}</code>\n"
                f"💰 Rp {amount:,}\n"
                f"💳 {method.upper()} → <code>{target}</code>\n"
                f"🕒 {created_at:%d-%m %H:%M} UTC{flag}\n"
                f"────────────────────"
            )

        text += (
            "\n\n👉 Gunakan:\n"
            "<code>/wd_pending_detail &lt;id&gt;</code> untuk detail"
        )

        await message.reply(text, parse_mode=ParseMode.HTML)

        log.info(f"[WD_PENDING] admin={admin_id} count={len(rows)}")

    except Exception as e:
        log.error(f"[WD_PENDING] ERROR: {e}", exc_info=True)
        await message.reply("❌ Gagal mengambil data.")
