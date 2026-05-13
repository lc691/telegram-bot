from common.utils.table_utils import get_user_table
from configs.logging_setup import log
from db.connect import get_db_cursor

# =================== #
# === FUNGSI USER === #
# =================== #


def get_all_users(source: str, limit: int = 50):
    """
    Mengambil semua user dari sumber tertentu (tabel dinamis), dibatasi oleh limit.
    """
    try:
        user_table = get_user_table(source)
        with get_db_cursor() as (cursor, _):
            cursor.execute(
                f"""
                SELECT user_id, first_name, username, is_vip, vip_expired
                FROM {user_table}
                ORDER BY created_at DESC
                LIMIT %s
                """,
                (limit,),
            )
            return cursor.fetchall()
    except Exception as e:
        log.error("Gagal mengambil daftar user dari %s: %s", source, e, exc_info=True)
        return []


def get_users(
    offset: int = 0,
    limit: int = 10,
    only_vip: bool = False,
    only_active: bool = True,  # 👈 default cuma ambil user aktif
    search_username: str | None = None,
    source: str = "drac1n",
):
    try:
        with get_db_cursor() as (cursor, _):
            table = get_user_table(source)

            query = f"""
                SELECT user_id, first_name, username, is_vip, vip_expired
                FROM {table}
                WHERE TRUE
            """
            params = []

            if only_vip:
                query += " AND is_vip = TRUE"
            if only_active:
                query += " AND is_active = TRUE"
            if search_username:
                query += " AND LOWER(username) LIKE %s"
                params.append(f"%{search_username.lower()}%")

            query += " ORDER BY created_at DESC OFFSET %s LIMIT %s"
            params.extend([offset, limit])

            cursor.execute(query, tuple(params))
            return cursor.fetchall()
    except Exception as e:
        log.error("Gagal mengambil pengguna: %s", e, exc_info=True)
        return []


def count_users(
    only_vip: bool = False, search_username: str | None = None, source: str = "drac1n"
) -> int:
    """
    Menghitung jumlah user berdasarkan filter VIP dan pencarian username.
    """
    try:
        with get_db_cursor() as (cursor, _):
            table = get_user_table(source)

            query = f"SELECT COUNT(*) FROM {table} WHERE TRUE"
            params = []

            if only_vip:
                query += " AND is_vip = TRUE"
            if search_username:
                query += " AND LOWER(username) LIKE %s"
                params.append(f"%{search_username.lower()}%")

            cursor.execute(query, tuple(params))
            return cursor.fetchone()[0] or 0
    except Exception as e:
        log.error("Gagal menghitung pengguna: %s", e, exc_info=True)
        return 0


def check_user_exists(user_id: int, source: str = "drac1n") -> bool:
    """
    Mengecek apakah user dengan user_id ada di sumber (tabel) yang ditentukan.
    """
    try:
        table = "users" if source == "drac1n" else "users_utbk"

        with get_db_cursor() as (cursor, _):
            cursor.execute(
                f"SELECT 1 FROM {table} WHERE user_id = %s LIMIT 1", (user_id,)
            )
            return cursor.fetchone() is not None
    except Exception as e:
        log.error("Gagal cek keberadaan user user_id=%s: %s", user_id, e, exc_info=True)
        return False


def iterate_all_users(source: str = "drac1n", batch_size: int = 100):
    """
    Generator: Mengambil seluruh user aktif secara bertahap per batch.
    """
    offset = 0
    while True:
        batch = get_users(
            offset=offset, limit=batch_size, source=source, only_active=True
        )
        if not batch:
            break
        yield batch
        offset += batch_size


def activate_vip_days(user_id: int, days: int, source: str = "drac1n"):
    table = get_user_table(source)
    try:
        with get_db_cursor() as (cursor, conn):
            cursor.execute(
                f"""
                UPDATE {table}
                SET
                    is_vip = TRUE,
                    vip_start = CURRENT_TIMESTAMP,
                    vip_expired = CURRENT_TIMESTAMP + INTERVAL '%s days'
                WHERE user_id = %s
                """,
                (days, user_id),
            )
            conn.commit()
    except Exception as e:
        log.error("Gagal mengaktifkan VIP user_id=%s: %s", user_id, e, exc_info=True)


def deactivate_user(user_id: int, source: str = "drac1n"):
    """
    Tandai user jadi tidak aktif (misalnya blocked bot).
    """
    try:
        table = get_user_table(source)
        with get_db_cursor() as (cursor, conn):
            cursor.execute(
                f"UPDATE {table} SET is_active = FALSE WHERE user_id = %s",
                (user_id,),
            )
            conn.commit()
            log.info(f"[DB] User {user_id} ditandai tidak aktif (blocked).")
    except Exception as e:
        log.error(f"[DB] Gagal update is_active user {user_id}: {e}", exc_info=True)
