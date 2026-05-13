from common.bot_utils import get_table_name
from configs.logging_setup import log
from db.connect import get_db_cursor


def check_user_exists(user_id: int, source_bot: str = "drac1n") -> bool:
    """
    Pastikan user_id ada di tabel user sesuai source_bot.
    Jika belum ada, otomatis insert.
    """
    try:
        if not isinstance(user_id, int) or user_id <= 0:
            log.warning("[TRAKTEER] Invalid user_id=%s", user_id)
            return False

        table = get_table_name(source_bot)
        if not table:
            log.error("[TRAKTEER] Table not found for source_bot=%s", source_bot)
            return False

        with get_db_cursor() as (cursor, conn):
            cursor.execute(
                f"SELECT 1 FROM {table} WHERE user_id = %s LIMIT 1",
                (user_id,),
            )
            if cursor.fetchone():
                return True

            cursor.execute(
                f"INSERT INTO {table} (user_id) VALUES (%s)",
                (user_id,),
            )
            conn.commit()

            log.info(
                "[TRAKTEER] New user inserted table=%s user_id=%s",
                table,
                user_id,
            )
            return True

    except Exception:
        log.exception(
            "[TRAKTEER] Failed check/insert user user_id=%s source_bot=%s",
            user_id,
            source_bot,
        )
        return False
