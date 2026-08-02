from database.connection import get_db_cursor


def fetch_today_access(user_id: int) -> tuple[int, object | None]:
    with get_db_cursor() as (cursor, _):
        cursor.execute(
            """
            SELECT COUNT(DISTINCT file_id), MAX(last_played)
            FROM video_stats
            WHERE user_id = %s
              AND last_played::date = CURRENT_DATE
            """,
            (user_id,),
        )
        return cursor.fetchone() or (0, None)


def fetch_vip_purchases(user_id: int) -> int:
    with get_db_cursor() as (cursor, _):
        cursor.execute(
            """
            SELECT COUNT(*)
            FROM vip_logs
            WHERE target_user_id = %s
            """,
            (user_id,),
        )
        row = cursor.fetchone()
        return row[0] if row else 0
