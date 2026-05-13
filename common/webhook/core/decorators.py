from functools import wraps

from flask import jsonify

from configs.logging_setup import log
from db.connect import get_db_cursor


# =====================[ DECORATOR DB TRANSACTION ]=====================
def with_transaction(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            try:
                with get_db_cursor() as (_, conn):
                    conn.rollback()
            except Exception as rollback_err:
                log.error(f"[DB] Gagal rollback: {rollback_err}", exc_info=True)
            log.error(f"[DB] Error saat transaksi: {e}", exc_info=True)
            return jsonify({"error": "Internal Server Error"}), 500

    return wrapper
