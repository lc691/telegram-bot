from db.connect import get_db_cursor


def log_search_query(
    user_id: int, username: str | None, query: str, matched: bool = False
):
    with get_db_cursor() as (cursor, conn):
        cursor.execute(
            """
            INSERT INTO search_logs (user_id, username, query, matched)
            VALUES (%s, %s, %s, %s)
        """,
            (user_id, username, query, matched),
        )
        conn.commit()
