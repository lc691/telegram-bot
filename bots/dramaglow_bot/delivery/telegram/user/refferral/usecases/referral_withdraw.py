# ============================================
# referral_withdraw.py (FINAL – ACTION)
# ============================================

import re
from pyrogram.enums import ParseMode
from pyrogram.types import Message

from common.utils.admin_cache import admin_cache
from configs.logging_setup import log
from db.connect import get_db_cursor
from ......handlers.admin.referral.wd_admin_handler import (
    build_admin_buttons,
    build_admin_withdraw_message,
)

MIN_WD = 50_000
ALLOWED_METHODS = {"ovo", "dana", "gopay", "bank"}
WD_COOLDOWN_MINUTES = 15


# ============================
# HELPERS
# ============================
def validate_target(method: str, target: str) -> bool:
    if method == "bank":
        return len(target) >= 8 and any(c.isdigit() for c in target)
    return bool(re.match(r"^08[0-9]{8,11}$", target))


def has_recent_or_pending_withdraw(cursor, user_id: int) -> bool:
    cursor.execute(
        """
        SELECT 1
        FROM affiliate_withdraw_requests
        WHERE user_id = %s
          AND (
                status = 'pending'
                OR created_at > NOW() - make_interval(mins => %s)
          )
        LIMIT 1
        """,
        (user_id, WD_COOLDOWN_MINUTES),
    )
    return cursor.fetchone() is not None


# ============================
# MAIN HANDLER (ACTION)
# ============================
async def referral_withdraw_handler(message: Message):
    user = message.from_user
    if not user:
        return

    user_id = user.id
    client = message._client  # 🔑 ambil client dari context

    args = message.text.split()
    if len(args) < 4:
        return await message.reply(
            "📌 <b>Format Withdraw</b>\n"
            "<code>/r_wd &lt;metode&gt; &lt;jumlah&gt; &lt;tujuan&gt;</code>\n\n"
            "Contoh:\n"
            "<code>/r_wd ovo 100000 081234567890</code>",
            parse_mode=ParseMode.HTML,
        )

    method = args[1].lower()
    if method not in ALLOWED_METHODS:
        return await message.reply(
            "❌ Metode tidak valid.\nGunakan: ovo / dana / gopay / bank",
            parse_mode=ParseMode.HTML,
        )

    try:
        amount = int(args[2])
        if amount < MIN_WD:
            return await message.reply(
                f"⚠️ Minimal withdraw: <b>Rp {MIN_WD:,}</b>",
                parse_mode=ParseMode.HTML,
            )
    except ValueError:
        return await message.reply("❌ Nominal harus berupa angka.")

    target = args[3].strip()
    if not validate_target(method, target):
        return await message.reply(
            "❌ Tujuan tidak valid.\n"
            "E-Wallet: 08xxxxxxxx\n"
            "Bank: nomor rekening / nama bank",
            parse_mode=ParseMode.HTML,
        )

    try:
        with get_db_cursor(commit=True) as (cursor, _):

            # 1️⃣ Validasi user
            cursor.execute(
                """
                SELECT affiliate_balance, abuse_flag
                FROM users
                WHERE user_id = %s
                """,
                (user_id,),
            )
            row = cursor.fetchone()

            if not row:
                return await message.reply(
                    "❗ Akun belum terdaftar.\nSilakan kirim /start terlebih dahulu.",
                    parse_mode=ParseMode.HTML,
                )

            balance, abuse_flag = row

            if abuse_flag:
                return await message.reply(
                    "🚫 Akun kamu diblokir dari proses withdraw.",
                    parse_mode=ParseMode.HTML,
                )

            # 2️⃣ Pending / cooldown
            if has_recent_or_pending_withdraw(cursor, user_id):
                return await message.reply(
                    f"⏳ Masih ada withdraw pending / cooldown.\n"
                    f"Silakan tunggu {WD_COOLDOWN_MINUTES} menit.",
                    parse_mode=ParseMode.HTML,
                )

            if balance < amount:
                return await message.reply(
                    f"❌ Saldo tidak cukup.\n" f"Saldo kamu: <b>Rp {balance:,}</b>",
                    parse_mode=ParseMode.HTML,
                )

            # 3️⃣ Insert request
            cursor.execute(
                """
                INSERT INTO affiliate_withdraw_requests
                    (user_id, amount, method, target, status)
                VALUES (%s, %s, %s, %s, 'pending')
                RETURNING id
                """,
                (user_id, amount, method, target),
            )
            req_id = cursor.fetchone()[0]

            # 4️⃣ Deduct balance (atomic)
            cursor.execute(
                """
                UPDATE users
                SET affiliate_balance = affiliate_balance - %s
                WHERE user_id = %s
                  AND affiliate_balance >= %s
                """,
                (amount, user_id, amount),
            )

            if cursor.rowcount != 1:
                raise RuntimeError("Balance update failed")

        # 5️⃣ User notify
        await message.reply(
            f"✅ <b>Withdraw berhasil dibuat!</b>\n\n"
            f"ID: <code>{req_id}</code>\n"
            f"Metode: <b>{method.upper()}</b>\n"
            f"Jumlah: <b>Rp {amount:,}</b>\n"
            f"Tujuan: <code>{target}</code>\n"
            f"Status: <b>pending</b>\n\n"
            f"⏱ Estimasi proses 1x24 jam.",
            parse_mode=ParseMode.HTML,
        )

        # 6️⃣ Admin notify
        for admin_id in admin_cache.admin_ids:
            try:
                await client.send_message(
                    admin_id,
                    build_admin_withdraw_message(
                        req_id, user_id, amount, method, target
                    ),
                    reply_markup=build_admin_buttons(req_id),
                    parse_mode=ParseMode.HTML,
                )
            except Exception:
                log.warning("[WITHDRAW] admin notify failed admin=%s", admin_id)

        log.info("[WITHDRAW] OK user=%s id=%s amt=%s", user_id, req_id, amount)

    except Exception:
        log.exception("[WITHDRAW] fatal error user=%s", user_id)
        await message.reply(
            "❌ Terjadi kesalahan sistem.\nSilakan coba lagi nanti.",
            parse_mode=ParseMode.HTML,
        )
