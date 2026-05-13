# ============================================
# wd_history_handler.py
# ============================================

from datetime import datetime, timezone

from pyrogram import Client, filters
from pyrogram.enums import ParseMode

from common.utils.admin_cache import admin_cache
from configs.logging_setup import log
from db.connect import get_db_cursor

MAX_SHOW = 15


def is_admin(user_id: int) -> bool:
    return user_id in admin_cache.admin_ids


@Client.on_message(filters.command("wd_history") & filters.private)
async def wd_history_handler(client: Client, message):

    admin_id = message.from_user.id

    if not is_admin(admin_id):
        return await message.reply("🚫 Akses ditolak.")

    args = message.text.split()
    if len(args) != 2 or not args[1].isdigit():
        return await message.reply(
            "📌 Format:\n<code>/wd_history &lt;user_id&gt;</code>",
            parse_mode=ParseMode.HTML
        )

    target_user_id = int(args[1])

    try:
        with get_db_cursor() as (cursor, _):
            cursor.execute("""
                SELECT
                    id,
                    amount,
                    method,
                    target,
                    status,
                    created_at,
                    reviewed_at,
                    admin_id
                FROM affiliate_withdraw_requests
                WHERE user_id=%s
                ORDER BY created_at DESC
                LIMIT %s
            """, (target_user_id, MAX_SHOW))

            rows = cursor.fetchall()

        if not rows:
            return await message.reply(
                f"ℹ️ Tidak ada riwayat WD untuk user <code>{target_user_id}</code>.",
                parse_mode=ParseMode.HTML
            )

        total_amount = sum(r[1] for r in rows)

        text = (
            f"📜 <b>Withdraw History</b>\n"
            f"User: <code>{target_user_id}</code>\n"
            f"Max {MAX_SHOW} data\n"
            f"Total amount: Rp {total_amount:,}\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
        )

        now = datetime.now(timezone.utc)

        for (
            wd_id,
            amount,
            method,
            target,
            status,
            created_at,
            reviewed_at,
            admin_id
        ) in rows:

            status_icon = {
                "pending": "⏳",
                "approved": "✅",
                "rejected": "❌"
            }.get(status, "❓")

            age_min = int((now - created_at).total_seconds() / 60)

            text += (
                f"\n{status_icon} <b>{status.upper()}</b>\n"
                f"🆔 <code>{wd_id}</code>\n"
                f"💰 Rp {amount:,}\n"
                f"💳 {method.upper()} → <code>{target}</code>\n"
                f"🕒 Req: {created_at:%d-%m %H:%M} ({age_min}m ago)\n"
            )

            if status == "pending":
                text += "⚠️ <b>MENUNGGU TINDAKAN</b>\n"

            if reviewed_at:
                text += (
                    f"👮 Admin: <code>{admin_id}</code>\n"
                    f"📅 Rev: {reviewed_at:%d-%m %H:%M}\n"
                )

            text += "────────────────────"

        await message.reply(text, parse_mode=ParseMode.HTML)

        log.info(
            f"[WD_HISTORY] admin={admin_id} user={target_user_id} count={len(rows)}"
        )

    except Exception as e:
        log.error(f"[WD_HISTORY] ERROR: {e}", exc_info=True)
        await message.reply("❌ Gagal mengambil riwayat.")
