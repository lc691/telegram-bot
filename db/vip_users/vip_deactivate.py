# ========== VIP REMOVE ==========
from datetime import datetime, timedelta, timezone

from configs.logging_setup import log
from db.connect import get_db_cursor


def remove_vip(user_id: int, source_bot: str = "drac1n") -> dict:
    if source_bot not in {"drac1n", "utbk"}:
        log.error(f"[REMOVE_VIP] ❌ Bot tidak valid: {source_bot}")
        return {"success": False, "reason": "invalid_bot"}

    table = "users_utbk" if source_bot == "utbk" else "users"

    try:
        with get_db_cursor() as (cursor, conn):
            # Cek user dan status VIP
            cursor.execute(f"SELECT is_vip FROM {table} WHERE user_id = %s", (user_id,))
            row = cursor.fetchone()

            if not row:
                log.warning(
                    f"[REMOVE_VIP] ❌ User {user_id} tidak ditemukan di tabel {table}."
                )
                return {"success": False, "reason": "not_found"}

            is_vip = row[0]
            if not is_vip:
                log.info(
                    f"[REMOVE_VIP] ℹ️ User {user_id} di tabel {table} sudah bukan VIP."
                )
                # Tetap hapus di vip_users kalau ada
                cursor.execute(
                    """
                    DELETE FROM vip_users
                    WHERE user_id = %s AND source_bot = %s
                    """,
                    (user_id, source_bot),
                )
                conn.commit()
                return {"success": False, "reason": "already_non_vip"}

            # Update VIP di tabel users/users_utbk
            cursor.execute(
                f"""
                UPDATE {table}
                SET
                    is_vip = FALSE,
                    vip_start = NULL,
                    vip_expired = NULL,
                    vip_reminded = FALSE
                WHERE user_id = %s
                """,
                (user_id,),
            )
            conn.commit()

            if cursor.rowcount > 0:
                log.info(
                    f"[REMOVE_VIP] ✅ VIP user {user_id} berhasil dihapus dari tabel {table}."
                )
            else:
                log.warning(
                    f"[REMOVE_VIP] ⚠️ Query update tidak mempengaruhi baris manapun di tabel {table}."
                )
                return {"success": False, "reason": "not_found"}

            # Delete from vip_users
            cursor.execute(
                """
                DELETE FROM vip_users
                WHERE user_id = %s AND source_bot = %s
                """,
                (user_id, source_bot),
            )
            deleted_vip_users = cursor.rowcount
            conn.commit()

            if deleted_vip_users > 0:
                log.info(
                    f"[REMOVE_VIP] ✅ Data user {user_id} berhasil dihapus dari tabel vip_users (bot={source_bot})."
                )
            else:
                log.info(
                    f"[REMOVE_VIP] ℹ️ Data user {user_id} tidak ditemukan di tabel vip_users (bot={source_bot})."
                )

            return {"success": True}

    except Exception as e:
        log.exception(
            f"[REMOVE_VIP] ❌ Gagal menghapus VIP user {user_id} dari tabel {table}"
        )
        return {"success": False, "reason": "error"}


async def reset_user_vip(user_id: int):
    """
    Reset semua data VIP untuk user tertentu.

    Args:
        user_id: ID user yang datanya akan di-reset.
    """
    try:
        with get_db_cursor() as (cur, conn):
            # 1. Hapus semua log VIP
            cur.execute("DELETE FROM vip_logs WHERE target_user_id = %s", (user_id,))
            log.info(f"[RESET_VIP] Deleted vip_logs for user_id={user_id}")

            # 2. Hapus semua VIP aktif / riwayat di vip_users
            cur.execute("DELETE FROM vip_users WHERE user_id = %s", (user_id,))
            log.info(f"[RESET_VIP] Deleted vip_users for user_id={user_id}")

            # 3. Reset kolom VIP di users
            cur.execute(
                """
                UPDATE users
                SET is_vip = FALSE,
                    vip_expired = NULL,
                    vip_start = NULL,
                    vip_purchases = 0,
                    vip_reminded = FALSE,
                    vip_reward_7d = FALSE,
                    vip_expiry_notified = FALSE
                WHERE user_id = %s
                """,
                (user_id,),
            )
            log.info(f"[RESET_VIP] Reset users VIP fields for user_id={user_id}")

            # Commit perubahan
            conn.commit()
            log.info(f"[RESET_VIP] Commit successful for user_id={user_id}")

    except Exception as e:
        log.error(f"[RESET_VIP] Failed to reset VIP for user_id={user_id}: {e}")
        raise


def get_all_vips(bot: str = "drac1n"):
    table = "users_utbk" if bot == "utbk" else "users"
    try:
        with get_db_cursor() as (cursor, _):
            cursor.execute(
                f"""
                SELECT user_id, vip_expired, vip_reminded
                FROM {table}
                WHERE is_vip = TRUE
                ORDER BY vip_expired DESC
                LIMIT 50
                """
            )
            return cursor.fetchall()
    except Exception as e:
        log.error(f"[GET_ALL_VIPS] Gagal ambil data VIP dari {table}: {e}")
        return []


def get_expiring_vips(
    bot: str = "drac1n", days_ahead: int = 3, offset: int = 0, limit: int = 50
):
    """
    Ambil user VIP yang akan expired dalam `days_ahead` hari dari bot tertentu.

    :param bot: Nama bot (drac1n / utbk)
    :param days_ahead: Berapa hari ke depan yang dianggap 'mendekati expired'
    :param offset: Offset pagination
    :param limit: Limit pagination
    :return: List user VIP mendekati expired
    """
    table = "users_utbk" if bot == "utbk" else "users"
    now = datetime.now(timezone.utc)
    upper_bound = now + timedelta(days=days_ahead)

    try:
        with get_db_cursor() as (cursor, _):
            cursor.execute(
                f"""
                SELECT user_id, vip_expired, vip_reminded
                FROM {table}
                WHERE is_vip = TRUE
                  AND vip_expired IS NOT NULL
                  AND vip_expired BETWEEN %s AND %s
                ORDER BY vip_expired ASC
                LIMIT %s OFFSET %s
                """,
                (now, upper_bound, limit, offset),
            )
            return cursor.fetchall()
    except Exception as e:
        log.error(f"[EXPIRING_VIPS] Gagal ambil data VIP dari {table}: {e}")
        return []
