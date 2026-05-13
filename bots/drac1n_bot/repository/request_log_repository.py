from db.connect import get_db_cursor


def save_request_log(user_id, username, first_name, source_code, title):
    with get_db_cursor() as (cursor, conn):
        cursor.execute(
            """
            INSERT INTO request_logs (user_id, username, first_name, source_code, title)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (user_id, username, first_name, source_code, title),
        )
        conn.commit()
