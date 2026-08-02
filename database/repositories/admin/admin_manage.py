from datetime import datetime

import pytz

from configs.logging_setup import log
from database.connection import get_db_cursor

UTC = pytz.utc
NOW_UTC = datetime.now(UTC)


def add_admin_to_db(user_id: int, first_name: str, username: str) -> bool:
    """
    Tambahkan admin baru ke database. Abaikan jika user_id sudah ada.
    """
    try:
        with get_db_cursor() as (cursor, conn):
            cursor.execute(
                """
                INSERT INTO admins (user_id, first_name, username)
                VALUES (%s, %s, %s)
                ON CONFLICT (user_id) DO NOTHING
                """,
                (user_id, first_name, username),
            )
            conn.commit()
            if cursor.rowcount > 0:
                log.info("Admin ditambahkan: user_id=%s", user_id)
            else:
                log.info(
                    "Admin sudah ada, tidak ditambahkan ulang: user_id=%s", user_id
                )
            return cursor.rowcount > 0
    except Exception as e:
        log.error("Gagal tambah admin user_id=%s: %s", user_id, e, exc_info=True)
        return False


def remove_admin_from_db(user_id: int) -> bool:
    """
    Hapus admin dari database berdasarkan user_id.
    """
    try:
        with get_db_cursor() as (cursor, conn):
            cursor.execute("DELETE FROM admins WHERE user_id = %s", (user_id,))
            conn.commit()
            if cursor.rowcount > 0:
                log.info("Admin dihapus: user_id=%s", user_id)
            else:
                log.info("Admin tidak ditemukan untuk dihapus: user_id=%s", user_id)
            return cursor.rowcount > 0
    except Exception as e:
        log.error("Gagal hapus admin user_id=%s: %s", user_id, e, exc_info=True)
        return False


def update_admin_in_db(user_id: int, first_name: str, username: str) -> bool:
    """
    Perbarui data admin berdasarkan user_id.
    """
    try:
        with get_db_cursor() as (cursor, conn):
            cursor.execute(
                """
                UPDATE admins
                SET first_name = %s, username = %s
                WHERE user_id = %s
                """,
                (first_name, username, user_id),
            )
            conn.commit()
            if cursor.rowcount > 0:
                log.info("Admin diperbarui: user_id=%s", user_id)
            else:
                log.info(
                    "Tidak ada admin yang diperbarui (user_id tidak ditemukan): user_id=%s",
                    user_id,
                )
            return cursor.rowcount > 0
    except Exception as e:
        log.error("Gagal update admin user_id=%s: %s", user_id, e, exc_info=True)
        return False
