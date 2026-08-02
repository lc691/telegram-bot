import asyncio
from datetime import datetime, timezone

from pyrogram.enums import ParseMode

from configs.logging_setup import log
from database.connection import get_db_cursor


BOT = "drac1n"
BATCH_LIMIT = 50
CHECK_INTERVAL = 300  # 5 menit (lebih stabil dari 6 jam scheduler)


# =========================
# MAIN LOOP
# =========================
async def reminder_loop(client):
    log.info("[REMINDER] 🚀 ENTERPRISE MODE STARTED")

    while True:
        try:
            await process_batch(client)
        except Exception as e:
            log.exception("[REMINDER] LOOP CRASH: %s", e)

        await asyncio.sleep(CHECK_INTERVAL)


# =========================
# ATOMIC BATCH CLAIM
# =========================
def claim_vip_batch(limit: int):
    with get_db_cursor() as (cur, conn):
        cur.execute(
            """
            WITH selected AS (
                SELECT user_id
                FROM vip_users
                WHERE status = 'active'
                  AND end_date BETWEEN NOW() AND NOW() + INTERVAL '2 days'
                  AND reminder_status = 0
                ORDER BY end_date ASC
                LIMIT %s
                FOR UPDATE SKIP LOCKED
            )
            UPDATE vip_users v
            SET reminder_status = 1
            FROM selected s
            WHERE v.user_id = s.user_id
            RETURNING v.user_id, v.paket, v.end_date;
            """,
            (limit,),
        )

        rows = cur.fetchall()
        conn.commit()
        return rows


# =========================
# PROCESS BATCH
# =========================
async def process_batch(client):
    rows = claim_vip_batch(BATCH_LIMIT)

    log.info("[REMINDER] batch claimed=%s", len(rows))

    for user_id, paket, end_date in rows:
        try:
            await send_reminder(client, user_id, paket, end_date)
            mark_done(user_id)
        except Exception as e:
            log.warning("[REMINDER] SEND FAIL user=%s err=%s", user_id, e)
            rollback_reminder(user_id)


# =========================
# SEND MESSAGE
# =========================
async def send_reminder(client, user_id, paket, end_date):

    now = datetime.now(timezone.utc)
    remaining = (end_date - now).total_seconds()
    hours = max(1, int(remaining // 3600))

    await client.send_message(
        chat_id=user_id,
        text=(
            "⚠️ <b>VIP Akan Berakhir</b>\n"
            "═══════✦✧✦═══════\n\n"
            "📄 <b>Detail VIP Kamu</b>\n"
            f"├─ 📦 Paket   : <code>{paket}</code>\n"
            f"├─ 🗓️ Expired : <code>{end_date}</code>\n"
            f"└─ ⏳ Sisa    : {hours} jam\n"
            "═══════✦✧✦═══════\n\n"
            "💡 Perpanjang sekarang agar tidak terputus."
        ),
        parse_mode=ParseMode.HTML,
    )


# =========================
# MARK DONE (FINAL STATE)
# =========================
def mark_done(user_id: int):
    with get_db_cursor() as (cur, conn):
        cur.execute(
            """
            UPDATE vip_users
            SET reminder_status = 2
            WHERE user_id = %s
            """,
            (user_id,),
        )
        conn.commit()


# =========================
# ROLLBACK SAFETY
# =========================
def rollback_reminder(user_id: int):
    with get_db_cursor() as (cur, conn):
        cur.execute(
            """
            UPDATE vip_users
            SET reminder_status = 0
            WHERE user_id = %s
            """,
            (user_id,),
        )
        conn.commit()
