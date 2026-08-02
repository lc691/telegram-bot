from configs.logging_setup import log
from database.connection import get_db_cursor

from .constants import (
    DEFAULT_TZ,
    VIP_STATUS_ACTIVE,
    VIP_STATUS_EXPIRED,
    VIP_TABLE,
)


def deactivate_expired_vips_db(source_bot: str | None = None) -> int:
    try:
        with get_db_cursor() as (cursor, conn):
            condition = """
                status = %s
                AND end_date IS NOT NULL
                AND end_date <= (NOW() AT TIME ZONE %s)
            """
            params = [VIP_STATUS_ACTIVE, DEFAULT_TZ]

            if source_bot:
                condition += " AND source_bot = %s"
                params.append(source_bot)

            cursor.execute(
                f"""
                WITH expired AS (
                    SELECT id
                    FROM {VIP_TABLE}
                    WHERE {condition}
                    FOR UPDATE SKIP LOCKED
                )
                UPDATE {VIP_TABLE}
                SET status = %s,
                    updated_at = (NOW() AT TIME ZONE %s)
                WHERE id IN (SELECT id FROM expired)
                RETURNING user_id;
                """,
                [*params, VIP_STATUS_EXPIRED, DEFAULT_TZ],
            )

            count = len(cursor.fetchall())
            conn.commit()
            return count

    except Exception:
        log.error("[VIP QUERY] ❌ Deactivate expired VIP failed", exc_info=True)
        return 0


def set_vip_notified(user_id: int, value: bool, table: str):
    with get_db_cursor() as (cur, conn):
        cur.execute(
            f"UPDATE {table} SET vip_reminded = %s WHERE user_id = %s",
            (value, user_id),
        )
        conn.commit()
