from datetime import datetime

import pytz

from configs.logging_setup import log
from database.connection import get_db_cursor

UTC = pytz.utc
NOW_UTC = datetime.now(UTC)


def set_state(admin_id: int, step: str) -> None:
    """
    Menyimpan atau memperbarui state (langkah) admin berdasarkan admin_id.
    """
    try:
        with get_db_cursor() as (cursor, conn):
            cursor.execute(
                """
                INSERT INTO admin_state (admin_id, step)
                VALUES (%s, %s)
                ON CONFLICT (admin_id)
                DO UPDATE SET step = EXCLUDED.step
                """,
                (admin_id, step),
            )
            conn.commit()
            log.info("State admin_id=%s di-set ke '%s'", admin_id, step)
    except Exception as e:
        log.error("Gagal set_state admin_id=%s: %s", admin_id, e, exc_info=True)


def log_current_state(admin_id: int) -> None:
    """
    Logging state saat ini dari admin. Hanya digunakan untuk debug/logging.
    """
    try:
        with get_db_cursor() as (cursor, _):
            cursor.execute("SELECT * FROM admin_state WHERE admin_id = %s", (admin_id,))
            row = cursor.fetchone()
            if row:
                log.debug("State admin_id=%s: %s", admin_id, row)
            else:
                log.debug("State admin_id=%s tidak ditemukan", admin_id)
    except Exception as e:
        log.error("Gagal ambil state admin_id=%s: %s", admin_id, e, exc_info=True)
