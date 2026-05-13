import pytz

from configs.logging_setup import log
from db.connect import get_db_cursor

UTC = pytz.utc


def is_admin(user_id: int) -> bool:
    """Periksa apakah user_id merupakan admin."""
    try:
        with get_db_cursor() as (cursor, _):
            cursor.execute("SELECT 1 FROM admins WHERE user_id = %s", (user_id,))
            result = cursor.fetchone()
            log.info("is_admin check: user_id=%s, result=%s", user_id, result)
            return result is not None
    except Exception as e:
        log.error("Gagal cek is_admin user_id=%s: %s", user_id, e, exc_info=True)
        return False


def load_admin_ids() -> list[int]:
    """Muat semua user_id admin dari database."""
    try:
        with get_db_cursor() as (cursor, _):
            cursor.execute("SELECT user_id FROM admins")
            rows = cursor.fetchall()
            admin_ids = [row[0] for row in rows]
            log.info("Admin IDs loaded: %s", admin_ids)
            return admin_ids
    except Exception as e:
        log.error("Gagal memuat admin IDs: %s", e, exc_info=True)
        return []
