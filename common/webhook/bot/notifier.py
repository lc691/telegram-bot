# webhook/bot/notifier.py

from datetime import datetime

from pyrogram.enums import ParseMode

from configs.logging_setup import log
from db.admin.admin_query import get_all_admins


async def notify_user_reminder(
    client, user_id, paket, is_extend, expired, total, remaining_days
):
    try:
        status_line = (
            "😊 <b>Lanjut terus! VIP kamu diperpanjang otomatis~</b>"
            if bool(is_extend)
            else "🥳 <b>Hore! VIP kamu baru aja aktif!</b>"
        )
        await client.send_message(
            chat_id=user_id,
            text=(
                f"🌟 <b>VIP Aktif!</b> 🌟\n\n"
                f"────────────────────\n"
                f"📦 <b>Paket:</b> <code>{paket.upper()}</code>\n"
                f"{status_line}\n\n"
                f"🗓️ <b>Sampai:</b> <code>{expired.strftime('%Y-%m-%d %H:%M:%S')}</code>\n"
                f"⏳ <b>Sisa waktu:</b> {remaining_days} hari\n"
                f"🔢 <b>Total beli:</b> <code>{total}x</code>\n"
                f"────────────────────\n"
                f"🎬 Yuk lanjut nonton tanpa gangguan!"
            ),
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
        )
    except Exception as e:
        log.warning(f"[NOTIF] Gagal kirim ke user {user_id}: {e}")


async def notify_admins_reminder(client, user_id, expiry_date):
    try:
        admins = get_all_admins()
        now = datetime.now(expiry_date.tzinfo or datetime.utcnow().astimezone().tzinfo)
        time_left = expiry_date - now
        hours_left = time_left.total_seconds() // 3600
        minutes_left = (time_left.total_seconds() % 3600) // 60

        text = (
            f"⚠️ <b>Reminder VIP</b>\n\n"
            f"👤 User [<code>{user_id}</code>](tg://user?id={user_id}) akan kehilangan akses VIP dalam "
            f"<b>{int(hours_left)} jam {int(minutes_left)} menit<b>.\n"
            f"📅 Expired: `{expiry_date.strftime('%Y-%m-%d %H:%M:%S')}`"
        )

        for admin in admins:
            try:
                await client.send_message(
                    chat_id=admin["user_id"],
                    text=text,
                    parse_mode=ParseMode.HTML,
                )
                log.info(f"[NOTIF] Reminder dikirim ke admin {admin['user_id']}")
            except Exception as e:
                log.warning(f"[NOTIF] Gagal ke admin {admin['user_id']}: {e}")
    except Exception as e:
        log.error(f"[NOTIF] Error kirim notifikasi admin: {e}")
