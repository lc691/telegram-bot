from pyrogram import Client, filters
from pyrogram.enums import ParseMode

from common.utils.admin_cache import admin_cache
from db.connect import get_db_cursor


@Client.on_message(filters.command("admin_audit") & filters.private)
async def admin_audit_view(client, message):
    if message.from_user.id not in admin_cache.admin_ids:
        return

    limit = 10
    args = message.text.split()
    if len(args) > 1 and args[1].isdigit():
        limit = min(int(args[1]), 50)

    with get_db_cursor() as (cursor, _):
        cursor.execute("""
            SELECT admin_id, action, target_type, target_id, created_at
            FROM affiliate_admin_audit_logs
            ORDER BY created_at DESC
            LIMIT %s
        """, (limit,))
        rows = cursor.fetchall()

    if not rows:
        return await message.reply("📭 Audit log kosong.")

    text = "🧾 <b>Admin Audit Log</b>\n━━━━━━━━━━━━━━\n"

    for admin_id, action, ttype, tid, ts in rows:
        text += (
            f"👮 <code>{admin_id}</code>\n"
            f"• Action: <b>{action}</b>\n"
            f"• Target: {ttype} → <code>{tid}</code>\n"
            f"• Time: {ts}\n\n"
        )

    await message.reply(text, parse_mode=ParseMode.HTML)
