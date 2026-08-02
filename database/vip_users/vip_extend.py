from datetime import datetime

from psycopg2 import errors

from shared.bot_utils import get_table_name
from configs.logging_setup import log
from configs.timezone import JAKARTA_TZ
from database.connection import get_dict_cursor as get_db_cursor
from database.vip_users.vip_db_utils import get_vip_package_info

from ..repositories.vip.queries_user import ensure_user_exists, get_active_vip_row
from ..repositories.vip.queries_vip import (
    insert_vip_log,
    upsert_vip_user,
)
from ..repositories.vip.vip_date_logic import calculate_dates


def extend_or_activate_vip(
    user_id: int,
    paket: str,
    admin_id: int,
    username: str = None,
    source_bot: str = "drac1n",
    keterangan: str = "Perpanjangan manual",
    update_user_table: bool = True,
):
    """
    Extend atau aktifkan VIP user.
    Mengikuti standar logika VIP refactor:
    - Tidak ada VIP → baru
    - Masih aktif → extend dari expired lama
    - Sudah expired → reset dari sekarang
    """

    now = datetime.now(JAKARTA_TZ)

    try:
        # ambil info paket
        paket_info = get_vip_package_info(paket)
        if not paket_info:
            return {"success": False, "reason": "invalid_paket"}

        paket_name, basic_days, total_days = paket_info
        durasi_hari = total_days

        with get_db_cursor() as (cur, conn):
            # pastikan user ada
            ensure_user_exists(cur, user_id, username)

            # cek vip sekarang
            row = get_active_vip_row(cur, user_id, source_bot)

            # hitung tanggal
            info = calculate_dates(now, row, durasi_hari)
            log.debug(f"[VIP] EXT/ACT DATE INFO: {info}")

            # upsert vip_users
            upsert_vip_user(
                cur,
                user_id,
                username,
                info["start"],
                info["end"],
                paket_name,
                source_bot,
            )

            # log vip
            insert_vip_log(
                cur,
                {
                    "user_id": user_id,
                    "admin_id": admin_id,
                    "paket": paket_name,
                    "basic_days": basic_days,
                    "bonus_days": 0,
                    "durasi": durasi_hari,
                    "is_extend": info["is_extend"],
                    "expired": info["end"],
                    "ket": keterangan,
                    "source": "manual",
                    "source_bot": source_bot,
                    "target_bot": source_bot,
                    "batch": None,
                    "promo": False,
                },
            )

            # optional update user table
            if update_user_table:
                table = get_table_name(source_bot)
                if table:
                    cur.execute(
                        f"""
                        UPDATE {table}
                        SET is_vip = TRUE,
                            vip_expired = %s,
                            vip_start = COALESCE(vip_start, %s),
                            vip_purchases = COALESCE(vip_purchases, 0) + 1,
                            updated_at = NOW()
                        WHERE user_id = %s
                        """,
                        (info["end"], now, user_id),
                    )

            conn.commit()

        log.info(
            f"[VIP] EXT/ACT OK user={user_id} paket={paket_name} "
            f"mode={'extend' if info['is_extend'] else 'baru'} "
            f"expired={info['end']}"
        )

        return {
            "success": True,
            "paket": paket_name,
            "duration": durasi_hari,
            "expired_at": info["end"],
            "is_extend": info["is_extend"],
            "is_new": not info["is_extend"],
            "mode": "extend" if info["is_extend"] else "baru",
            "expired_lama": info["expired_lama"],
            "user_id": user_id,
        }

    except errors.UniqueViolation:
        return {"success": False, "reason": "duplicate"}

    except Exception as e:
        log.exception(f"[VIP] EXT/ACT FAILED user={user_id}")
        return {"success": False, "reason": str(e), "user_id": user_id}
