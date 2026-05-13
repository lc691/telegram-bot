from datetime import datetime

import pytz

from configs.logging_setup import log
from db.connect import get_db_cursor

UTC = pytz.utc
NOW_UTC = datetime.now(UTC)


def get_admin_by_user_id(user_id: int):
    """Ambil data admin berdasarkan user_id."""
    try:
        with get_db_cursor() as (cursor, _):
            cursor.execute(
                "SELECT user_id, first_name, username FROM admins WHERE user_id = %s",
                (user_id,),
            )
            row = cursor.fetchone()
            log.info("Ambil admin user_id=%s: %s", user_id, row)
            return row
    except Exception as e:
        log.error("Gagal ambil admin user_id=%s: %s", user_id, e, exc_info=True)
        return None


def get_all_admins(default_name: str = "-"):
    """
    Ambil seluruh data admin.
    Parameter:
        default_name: Nilai default untuk first_name jika None.
    """
    try:
        with get_db_cursor() as (cursor, _):
            cursor.execute(
                "SELECT user_id, first_name, username FROM admins ORDER BY user_id"
            )
            rows = cursor.fetchall()
            result = [
                {
                    "user_id": row[0],
                    "first_name": row[1] or default_name,
                    "username": row[2] or None,
                }
                for row in rows
            ]
            log.info("Data semua admin berhasil diambil.")
            return result
    except Exception as e:
        log.error("Gagal ambil data semua admin: %s", e, exc_info=True)
        return []
