# ========== VIP TRANSACTION LOG ==========
from datetime import datetime, timezone

from configs.logging_setup import log
from db.connect import get_db_cursor


def log_vip_transaction(
    target_user_id: int,
    admin_user_id: int,
    paket: str,
    durasi_hari: int,
    expired_baru,
    is_extend: bool = False,
    keterangan: str = None,
    source_bot: str = None,
) -> bool:
    try:
        # Pastikan expired_baru adalah objek datetime dengan timezone UTC
        if isinstance(expired_baru, str):
            expired_baru = datetime.fromisoformat(expired_baru)
        if expired_baru.tzinfo is None:
            expired_baru = expired_baru.replace(tzinfo=timezone.utc)

        with get_db_cursor() as (cursor, conn):
            cursor.execute(
                """
                INSERT INTO vip_logs (
                    target_user_id, admin_user_id, paket, durasi_hari,
                    is_extend, expired_baru, keterangan, source_bot, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
                """,
                (
                    target_user_id,
                    admin_user_id,
                    paket,
                    durasi_hari,
                    is_extend,
                    expired_baru,
                    keterangan,
                    source_bot,
                ),
            )
            conn.commit()

        log.info(
            f"[VIP LOG] ✅ Log VIP berhasil dicatat untuk user_id={target_user_id} | bot={source_bot}"
        )
        return True

    except Exception as e:
        log.error(
            f"[VIP LOG] ❌ Gagal mencatat log VIP untuk user_id={target_user_id}: {e}",
            exc_info=True,
        )
        return False


def get_vip_logs_for_user(user_id: int) -> list[dict]:
    try:
        with get_db_cursor() as (cursor, _):
            cursor.execute(
                """
                SELECT paket, durasi_hari, is_extend, expired_baru, created_at
                FROM vip_logs
                WHERE target_user_id = %s
                ORDER BY created_at DESC
                LIMIT 10
                """,
                (user_id,),
            )
            rows = cursor.fetchall()

        return [
            {
                "paket": row[0],
                "durasi_hari": row[1],
                "is_extend": bool(row[2]),
                "expired_baru": format_datetime(row[3]),
                "created_at": format_datetime(row[4]),
            }
            for row in rows
        ]

    except Exception as e:
        log.error(
            f"[VIP LOGS] ❌ Gagal ambil log VIP user_id={user_id}: {e}", exc_info=True
        )
        return []


def format_datetime(dt):
    if isinstance(dt, datetime):
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    return str(dt)
