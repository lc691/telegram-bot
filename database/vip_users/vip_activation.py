from datetime import datetime

from configs.logging_setup import log
from configs.timezone import JAKARTA_TZ
from database.connection import get_dict_cursor

from ..repositories.vip.queries_user import ensure_user_exists, get_active_vip_row
from ..repositories.vip.queries_vip import count_user_purchases, insert_vip_log, upsert_vip_user
from ..repositories.vip.validators import calculate_total_duration
from ..repositories.vip.vip_date_logic import calculate_dates


def safe_insert_vip_user(
    user_id: int,
    username: str,
    paket: str,
    durasi_hari: int = None,
    basic_days: int = 0,
    bonus_days: int = 0,
    keterangan: str = "",
    source: str = "manual",
    source_bot: str = "drac1n",
    target_bot: str = "drac1n",
    admin_id: int = 0,
    batch_uuid: str = None,
    is_promo_once: bool = False,
):
    """
    Tambah atau extend VIP user dengan aman,
    TANPA menyentuh kolom turunan users.vip_purchases.
    """
    now = datetime.now(JAKARTA_TZ)
    durasi_hari = calculate_total_duration(durasi_hari, basic_days, bonus_days)

    try:
        with get_dict_cursor() as (cur, conn):
            log.info(
                "[VIP] START user=%s paket=%s durasi=%s basic=%s bonus=%s",
                user_id, paket, durasi_hari, basic_days, bonus_days
            )

            # 1️⃣ Pastikan user ada
            ensure_user_exists(cur, user_id, username)

            # 2️⃣ Ambil VIP aktif (kecuali promo once)
            row = None
            if not is_promo_once:
                row = get_active_vip_row(cur, user_id, source_bot)

            # 3️⃣ Hitung tanggal start & expired
            info = calculate_dates(now, row, durasi_hari)

            # Tentukan mode (INI FIX UTAMA)
            mode = "extend" if info.get("is_extend") else "baru"

            # 4️⃣ Upsert vip_users
            upsert_vip_user(
                cur,
                user_id,
                username,
                info["start"],
                info["end"],
                paket,
                source_bot
            )

            # 5️⃣ Insert vip_logs
            log_row = insert_vip_log(cur, {
                "user_id": user_id,
                "admin_id": admin_id,
                "paket": paket,
                "basic_days": basic_days,
                "bonus_days": bonus_days,
                "durasi": durasi_hari,
                "is_extend": info["is_extend"],
                "expired": info["end"],
                "ket": keterangan,
                "source": source,
                "source_bot": source_bot,
                "target_bot": target_bot,
                "batch": batch_uuid,
                "promo": is_promo_once,
            })

            # 6️⃣ Hitung durasi rinci
            delta = info["end"] - info["start"]
            duration_detail = {
                "days": delta.days,
                "hours": delta.seconds // 3600,
                "minutes": (delta.seconds % 3600) // 60
            }

            conn.commit()

            # 7️⃣ Hitung total pembelian (READ-ONLY, aman)
            purchases = count_user_purchases(cur, user_id)

            return {
                "success": True,
                "user_id": user_id,
                "paket": paket,
                "mode": mode,                     # ✅ FIX PENTING
                "start_at": info["start"],
                "expired_at": info["end"],
                "duration_detail": duration_detail,
                "is_extend": info["is_extend"],
                "expired_lama": info.get("expired_lama"),
                "promo_once": is_promo_once,
                "batch_uuid": batch_uuid,
                "log_id": log_row["id"] if log_row else None,
                "total_purchases": purchases,
            }

    except Exception as e:
        log.exception("[VIP] ERROR safe_insert_vip_user user_id=%s", user_id)
        return {
            "success": False,
            "reason": "db_error",
            "error": str(e),
            "user_id": user_id,
        }
