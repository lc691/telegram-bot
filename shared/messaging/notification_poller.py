import asyncio

from datetime import datetime, timezone

from pyrogram.enums import ParseMode

from shared.messaging.email_responder import send_email_reply_async
from shared.messaging.vip_message_builder import (
    generate_vip_message_to_admin,
    generate_vip_message_to_user,
)
from shared.utils.admin_notifier import notify_admin_error, notify_admin_warning
from config import SPECIAL_DONORS
from configs.logging_setup import log
from database.repositories.admin.admin_query import get_all_admins
from database.connection import get_db_cursor

_notifier_started_bots = set()


async def notify_vip_from_logs(client, bot_name):
    try:
        with get_db_cursor() as (cursor, conn):
            cursor.execute(
                """
                SELECT id, target_user_id, paket, expired_baru, durasi_hari,
                       is_extend, created_at
                FROM vip_logs
                WHERE is_notified = FALSE
                  AND source_bot = %s
                  AND created_at > NOW() - INTERVAL '5 MINUTE'
                ORDER BY created_at DESC
                """,
                (bot_name,),
            )
            rows = cursor.fetchall()

            for row in rows:
                log_id, user_id, paket, expired_baru, durasi_hari, is_extend, _ = row

                if isinstance(expired_baru, str):
                    expired_baru = datetime.fromisoformat(expired_baru)

                cursor.execute(
                    "SELECT first_name, username, vip_start, vip_purchases FROM users WHERE user_id = %s",
                    (user_id,),
                )
                user_row = cursor.fetchone() or (
                    "User",
                    "-",
                    datetime.now(timezone.utc),
                    1,
                )
                first_name, username, vip_start, purchases = user_row

                if isinstance(vip_start, str):
                    vip_start = datetime.fromisoformat(vip_start)

                try:
                    nominal = int("".join(filter(str.isdigit, paket)))
                except ValueError:
                    nominal = durasi_hari
                bonus = durasi_hari - nominal

                msg_user = generate_vip_message_to_user(
                    first_name,
                    username,
                    user_id,
                    paket,
                    vip_start,
                    expired_baru,
                    is_extend=is_extend,
                    purchases=purchases,
                    bonus=bonus,
                )

                try:
                    await client.send_message(
                        chat_id=user_id,
                        text=msg_user,
                        parse_mode=ParseMode.HTML,
                    )
                    log.info(f"[NOTIF] VIP dikirim ke user {user_id}")
                except Exception as e:
                    log.warning(f"[NOTIF] Gagal kirim ke user {user_id}: {e}")
                    await notify_admin_warning(
                        client, f"⚠️ Gagal kirim VIP ke user `{user_id}`:\n{e}"
                    )

                msg_admin = generate_vip_message_to_admin(
                    first_name, username, user_id, paket, purchases, is_extend
                )
                for admin in get_all_admins():
                    try:
                        await client.send_message(
                            chat_id=admin["user_id"],
                            text=msg_admin,
                            parse_mode=ParseMode.HTML,
                        )
                        log.info(f"[NOTIF] VIP notifikasi ke admin {admin['user_id']}")
                    except Exception as e:
                        log.warning(
                            f"[NOTIF] Gagal kirim ke admin {admin['user_id']}: {e}"
                        )
                        await notify_admin_warning(
                            client,
                            f"⚠️ Gagal kirim VIP ke admin `{admin['user_id']}`:\n{e}",
                        )

                cursor.execute(
                    "UPDATE vip_logs SET is_notified = TRUE WHERE id = %s", (log_id,)
                )
                conn.commit()
                log.info(f"[NOTIF] Log VIP id={log_id} ditandai sebagai notified.")

    except Exception as e:
        msg = f"❌ Gagal proses vip_logs untuk bot `{bot_name}`:\n{e}"
        log.exception(msg)
        await notify_admin_error(client, msg)


async def notify_donasi_from_log(client, bot_name):
    try:
        with get_db_cursor() as (cursor, conn):
            cursor.execute(
                """
                SELECT id, email, amount, message, timestamp
                FROM donation_log
                WHERE type = 'donasi' AND is_notified = FALSE
                  AND source_bot = %s
                  AND timestamp > NOW() - INTERVAL '5 MINUTE'
                ORDER BY timestamp DESC
                """,
                (bot_name,),
            )
            rows = cursor.fetchall()

            for row in rows:
                log_id, email, amount, message, timestamp = row

                msg_admin = (
                    f"🎉 <b>Donasi Masuk!</b>\n\n"
                    f"📧 Email: <code>{email}</code>\n"
                    f"💵 Jumlah: <code>{amount}</code>\n"
                    f"📝 Pesan: _{message or '-'}_"
                )

                for admin in get_all_admins():
                    try:
                        await client.send_message(
                            chat_id=admin["user_id"],
                            text=msg_admin,
                            parse_mode=ParseMode.HTML,
                        )
                    except Exception as e:
                        log.warning(
                            f"[NOTIF] Gagal kirim ke admin {admin['user_id']}: {e}"
                        )
                        await notify_admin_warning(
                            client,
                            f"⚠️ Gagal kirim notifikasi donasi ke admin `{admin['user_id']}`:\n{e}",
                        )

                if reply := SPECIAL_DONORS.get(email):
                    try:
                        send_email_reply_async(email, reply)
                    except Exception as e:
                        log.warning(
                            f"[NOTIF] Gagal kirim email balasan ke {email}: {e}"
                        )
                        await notify_admin_warning(
                            client,
                            f"⚠️ Gagal kirim email balasan ke `{email}`:\n{e}",
                        )

                cursor.execute(
                    "UPDATE donation_log SET is_notified = TRUE WHERE id = %s",
                    (log_id,),
                )
                conn.commit()

    except Exception as e:
        msg = f"❌ Gagal proses donation_log untuk bot `{bot_name}`:\n{e}"
        log.exception(msg)
        await notify_admin_error(client, msg)


async def run_notifier_loop(app, bot_name):
    if bot_name in _notifier_started_bots:
        log.warning(f"[NOTIFIER] ❗ Notifikasi untuk '{bot_name}' sudah berjalan.")
        return

    _notifier_started_bots.add(bot_name)
    # log.info(f"📡 Loop notifikasi dimulai untuk bot '{bot_name}'")

    while True:
        try:
            await notify_vip_from_logs(app, bot_name)
            await notify_donasi_from_log(app, bot_name)
        except Exception as e:
            msg = f"[{bot_name}] ❌ Loop notifikasi error:\n{e}"
            log.error(msg, exc_info=True)
            await notify_admin_error(app, msg)

        await asyncio.sleep(10)
