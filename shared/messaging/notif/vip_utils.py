from datetime import datetime, timedelta, timezone
from typing import Literal
from zoneinfo import ZoneInfo

from configs.logging_setup import log
from database.connection import get_db_cursor

# Zona WIB

JAKARTA_TZ = ZoneInfo("Asia/Jakarta")


def get_basic_days(paket: str) -> int:
    """
    Ambil durasi dasar paket VIP dari tabel vip_packages.
    Return 0 kalau paket tidak ditemukan / non-aktif.
    """
    try:
        with get_db_cursor() as (cur, _):
            cur.execute(
                """
                SELECT basic_days
                FROM vip_packages
                WHERE paket_name = %s
                  AND is_active = TRUE
                LIMIT 1
                """,
                (paket,),
            )
            row = cur.fetchone()
            if not row:
                log.warning(
                    "[VIP_UTILS] ⚠️ Paket %s tidak ditemukan / non-aktif → return 0", paket
                )
                return 0
            return int(row[0])
    except Exception as e:
        log.exception("[VIP_UTILS] Error get_basic_days paket=%s", paket)
        return 0


def get_last_vip_end(user_id: int) -> datetime | None:
    """
    Ambil VIP terakhir user (end_date terbesar).
    Tidak menentukan aktif / expired.
    Hasil dijamin timezone-aware (Asia/Jakarta).
    """
    try:
        with get_db_cursor() as (cur, _):
            cur.execute(
                """
                SELECT end_date
                FROM vip_users
                WHERE user_id = %s
                ORDER BY end_date DESC
                LIMIT 1
                """,
                (user_id,),
            )
            row = cur.fetchone()

        if row and isinstance(row[0], datetime):
            vip_end = row[0]
            # Pastikan timezone-aware
            if vip_end.tzinfo is None:
                vip_end = vip_end.replace(tzinfo=JAKARTA_TZ)
            else:
                vip_end = vip_end.astimezone(JAKARTA_TZ)
        else:
            vip_end = None

        log.debug("[VIP_UTILS] user_id=%s, last_vip_end=%s", user_id, vip_end)
        return vip_end
    except Exception as e:
        log.exception("[VIP_UTILS] Error get_last_vip_end user_id=%s", user_id)
        return None



def calculate_new_vip_end(
    old_vip_end: datetime | None,
    basic_days: int,
    bonus_days: int = 0,
    tx_time: datetime | None = None,
    via_voucher: bool = False,
) -> tuple[datetime, Literal["baru", "extend"]]:
    """
    Hitung VIP baru dengan mode 'baru' atau 'extend'.

    - Semua perhitungan berbasis WIB
    - VIP expired → BARU
    - VIP aktif → EXTEND
    - Return expired dalam UTC (siap DB)
    """

    # ======================================================
    # 1️⃣ WAKTU TRANSAKSI (WIB, WAJIB AWARE)
    # ======================================================
    if tx_time is None:
        tx_time = datetime.now(JAKARTA_TZ)
    elif tx_time.tzinfo is None:
        tx_time = tx_time.replace(tzinfo=JAKARTA_TZ)
    else:
        tx_time = tx_time.astimezone(JAKARTA_TZ)

    # ======================================================
    # 2️⃣ NORMALISASI VIP LAMA (DEFENSIVE)
    # ======================================================
    if old_vip_end:
        if old_vip_end.tzinfo is None:
            old_vip_end = old_vip_end.replace(tzinfo=JAKARTA_TZ)
        else:
            old_vip_end = old_vip_end.astimezone(JAKARTA_TZ)

    # ======================================================
    # 3️⃣ TENTUKAN MODE & BASE START
    # ======================================================
    if old_vip_end and old_vip_end > tx_time:
        mode: Literal["extend", "baru"] = "extend"
        base_start = old_vip_end
    else:
        mode = "baru"
        base_start = tx_time

    # ======================================================
    # 4️⃣ HITUNG TOTAL HARI
    # ======================================================
    total_days = basic_days if via_voucher else (basic_days + bonus_days)
    total_days = max(1, total_days)

    # ======================================================
    # 5️⃣ HITUNG EXPIRED (WIB → UTC)
    # ======================================================
    new_local_end = base_start + timedelta(days=total_days)
    new_end_utc = new_local_end.astimezone(timezone.utc)

    log.debug(
        "[VIP_CALC] mode=%s base_start=%s days=%s expired_wib=%s expired_utc=%s",
        mode,
        base_start,
        total_days,
        new_local_end,
        new_end_utc,
    )

    return new_end_utc, mode
