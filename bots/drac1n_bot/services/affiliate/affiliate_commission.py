import os

from datetime import datetime, timezone
from pyrogram.enums import ParseMode
from configs.logging_setup import log
from db.affiliate_db import detect_affiliate_abuse
from db.connect import get_db_cursor

AFFILIATE_RATE = float(os.getenv("AFFILIATE_RATE", "0.2"))  # mudah diganti

async def process_affiliate_commission(app, user_id, paket, price, source_bot, tx_id=None):

    # =================================================
    # EARLY EXIT: promo / free / invalid price
    # =================================================
    if price <= 0:
        log.info(f"[AFFILIATE] Skip commission (promo/free) user={user_id}")
        return

    if not tx_id:
        log.warning("[AFFILIATE] Missing tx_id → commission skipped")
        return

    with get_db_cursor(commit=True) as (cursor, _):

        # -----------------------------
        # Get referrer (locked)
        # -----------------------------
        cursor.execute("""
            SELECT u.referrer_user_id, a.is_admin
            FROM users u
            LEFT JOIN admins a ON a.user_id = u.referrer_user_id
            WHERE u.user_id=%s
            FOR UPDATE
        """, (user_id,))

        row = cursor.fetchone()
        if not row or not row[0]:
            return

        referrer, is_admin = row

        # Admin cannot earn
        if is_admin:
            log.warning(f"[AFFILIATE] Admin referrer blocked id={referrer}")
            return

        # Self referral guard
        if referrer == user_id:
            log.error("[AFFILIATE] Self referral detected")
            return

        # -----------------------------
        # Idempotency guard
        # -----------------------------
        cursor.execute("""
            SELECT 1 FROM affiliate_commission_logs
            WHERE tx_id=%s LIMIT 1
        """, (tx_id,))

        if cursor.fetchone():
            log.warning(f"[AFFILIATE] Duplicate commission blocked tx={tx_id}")
            return

        # -----------------------------
        # 💰 Calculate commission
        # -----------------------------
        commission = int(price * AFFILIATE_RATE)

        # -----------------------------
        # Abuse check
        # -----------------------------
        is_sus, score, reasons = detect_affiliate_abuse(
            cursor, user_id, referrer, price, datetime.now(timezone.utc), source_bot
        )

        # -----------------------------
        # Log creation
        # -----------------------------
        cursor.execute("""
            INSERT INTO affiliate_commission_logs
                (tx_id, referred_user_id, referrer_user_id,
                 paket, price, commission, source_bot, tx_time, status)
            VALUES (%s,%s,%s,%s,%s,%s,%s,now(), 'pending')
            RETURNING id
        """, (tx_id, user_id, referrer, paket, price, commission, source_bot))

        log_id = cursor.fetchone()[0]

        if is_sus:
            cursor.execute("""
                UPDATE affiliate_commission_logs
                SET status='withheld', abuse_score=%s, notes=%s
                WHERE id=%s
            """, (score, ",".join(reasons), log_id))

            return

        # -----------------------------
        # 💸 Atomic payout
        # -----------------------------
        cursor.execute("""
            UPDATE users
            SET affiliate_balance = affiliate_balance + %s,
                affiliate_total_earned = affiliate_total_earned + %s
            WHERE user_id=%s
        """, (commission, commission, referrer))

        cursor.execute("""
            UPDATE affiliate_commission_logs SET status='paid'
            WHERE id=%s
        """, (log_id,))

    # -----------------------------
    # Notification (outside tx)
    # -----------------------------
    try:
        await app.send_message(
            chat_id=referrer,
            text=(
                f"🎉 Komisi affiliate masuk!\n"
                f"User: <code>{user_id}</code>\n"
                f"Paket: <b>{paket}</b>\n"
                f"Komisi: Rp {commission:,}"
            ),
            parse_mode=ParseMode.HTML,
        )
    except:
        pass
