# ========== VIP RESET ==========
from datetime import datetime

from configs.logging_setup import log
from database.connection import get_db_cursor


def reset_vip(user_id: int = None):
    try:
        with get_db_cursor() as (cursor, conn):
            if user_id:
                cursor.execute(
                    """
                    UPDATE users
                    SET is_vip = FALSE, vip_start = NULL, vip_expired = NULL, vip_reminded = FALSE
                    WHERE user_id = %s
                """,
                    (user_id,),
                )
            else:
                cursor.execute(
                    """
                    UPDATE users
                    SET is_vip = FALSE, vip_start = NULL, vip_expired = NULL, vip_reminded = FALSE
                """
                )
            conn.commit()
    except Exception as e:
        log.error(f"❌ Gagal mereset VIP: {e}", exc_info=True)


def reset_vip_by_id(user_id: int) -> bool:
    try:
        with get_db_cursor() as (cursor, conn):
            cursor.execute(
                """
                UPDATE users
                SET is_vip = FALSE, vip_expired = NULL, vip_start = NULL, vip_reminded = FALSE
                WHERE user_id = %s
            """,
                (user_id,),
            )
            conn.commit()
            return cursor.rowcount > 0
    except Exception as e:
        log.error(f"[VIP RESET] Gagal reset VIP user {user_id}: {e}", exc_info=True)
        return False
