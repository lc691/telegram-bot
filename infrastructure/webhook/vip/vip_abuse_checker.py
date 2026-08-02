from datetime import datetime, timedelta, timezone

from configs.logging_setup import log
from database.connection import get_db_cursor

# ================================
# WIB TIMEZONE (UTC+7)
# ================================
WIB = timezone(timedelta(hours=7))

# ================================
# Thresholds
# ================================
MAX_DAILY_VIP_PURCHASE = 3
MAX_HOURLY_VIP_PURCHASE = 2
MIN_ACCOUNT_AGE_MINUTES = 5
MAX_REFERRALS_FIRST_HOUR = 3


def run_vip_abuse_checks(user_id: int, price: int):
    """
    Return:
        None → lanjut proses VIP
        str  → BLOCK + message
    """

    now = datetime.now(WIB)

    with get_db_cursor() as (cursor, _):

        # -----------------------------------------------------
        # 1. Flagged user (GLOBAL — tetap dicek)
        # -----------------------------------------------------
        cursor.execute(
            "SELECT abuse_flag, referrer_user_id, created_at FROM users WHERE user_id=%s",
            (user_id,),
        )
        row = cursor.fetchone()

        if not row:
            return None

        abuse_flag, referrer_user_id, created_at = row

        if abuse_flag:
            log.warning("[VIP-ABUSE] flagged user blocked user=%s", user_id)
            return "⚠️ Akun Anda diblokir karena aktivitas mencurigakan."

        # -----------------------------------------------------
        # ❗ EXIT CEPAT: TANPA REFERRAL → TIDAK CEK ABUSE
        # -----------------------------------------------------
        if not referrer_user_id:
            # hanya hard-rule global
            if price <= 1000:
                log.warning("[VIP-ABUSE] abnormal low price %s user=%s", price, user_id)
                return "⚠️ Harga VIP tidak valid."
            return None

        # =====================================================
        # ⬇️ SEMUA DI BAWAH INI KHUSUS USER DENGAN REFERRAL
        # =====================================================

        # -----------------------------------------------------
        # 2. New account protection
        # -----------------------------------------------------
        try:
            if created_at:
                if created_at.tzinfo is None:
                    created_at = created_at.replace(tzinfo=WIB)

                age_minutes = (now - created_at).total_seconds() / 60
                if age_minutes < MIN_ACCOUNT_AGE_MINUTES:
                    log.warning("[VIP-ABUSE] too new account user=%s", user_id)
                    return "⚠️ Akun terlalu baru untuk melakukan VIP."
        except Exception as e:
            log.error("[VIP-ABUSE] created_at parse error user=%s err=%s", user_id, e)

        # -----------------------------------------------------
        # 3. Hourly velocity
        # -----------------------------------------------------
        cursor.execute(
            """
            SELECT COUNT(*) FROM users
            WHERE user_id=%s
              AND vip_start > now() - interval '1 hour'
            """,
            (user_id,),
        )
        if cursor.fetchone()[0] >= MAX_HOURLY_VIP_PURCHASE:
            log.warning("[VIP-ABUSE] hourly limit user=%s", user_id)
            return "⚠️ Terlalu banyak pembelian VIP dalam waktu singkat."

        # -----------------------------------------------------
        # 4. Daily velocity
        # -----------------------------------------------------
        cursor.execute(
            """
            SELECT COUNT(*) FROM users
            WHERE user_id=%s
              AND vip_start > now() - interval '1 day'
            """,
            (user_id,),
        )
        if cursor.fetchone()[0] >= MAX_DAILY_VIP_PURCHASE:
            log.warning("[VIP-ABUSE] daily limit user=%s", user_id)
            return "⚠️ Batas pembelian VIP harian terlampaui."

        # -----------------------------------------------------
        # 5. Referrer farming detection
        # -----------------------------------------------------
        cursor.execute(
            """
            SELECT COUNT(*) FROM users
            WHERE referrer_user_id=%s
              AND vip_start > now() - interval '1 hour'
            """,
            (referrer_user_id,),
        )
        if cursor.fetchone()[0] >= MAX_REFERRALS_FIRST_HOUR:
            log.warning("[VIP-ABUSE] referrer flood user=%s", user_id)
            return "⚠️ Aktivitas referral terlalu cepat."

        # -----------------------------------------------------
        # 6. Abnormal price (tetap)
        # -----------------------------------------------------
        if price <= 1000:
            log.warning("[VIP-ABUSE] abnormal low price %s user=%s", price, user_id)
            return "⚠️ Harga VIP tidak valid."

        # -----------------------------------------------------
        # ✅ SAFE
        # -----------------------------------------------------
        return None
