from db.connect import get_dict_cursor


def fetch_all_genres() -> list[str]:
    with get_dict_cursor() as (cursor, _):
        cursor.execute(
            """
            SELECT DISTINCT genre
            FROM shows
            WHERE genre IS NOT NULL
            ORDER BY genre
            """
        )
        return [row["genre"] for row in cursor.fetchall() if row["genre"]]
