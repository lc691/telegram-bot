# domain/show_repository.py
from db.connect import get_dict_cursor, get_db_cursor


def get_show_with_latest_file_full(show_id: int) -> dict | None:
    with get_dict_cursor() as (cur, _):
        cur.execute(
            """
            SELECT
                s.id AS show_id,
                s.title AS title,
                f.channel_username,
                sf.message_id AS file_message_id
            FROM shows s
            JOIN show_files sf ON sf.show_id = s.id
            JOIN files f ON f.id = sf.file_id
            WHERE s.id = %s
              AND sf.message_id IS NOT NULL
            ORDER BY sf.message_id DESC
            LIMIT 1
            """,
            (show_id,),
        )

        row = cur.fetchone()
        if not row:
            return None

        return {
            "show_id": row["show_id"],
            "title": row["title"],
            "channel_username": row["channel_username"],
            "file_message_id": row["file_message_id"],
        }


def search_exact(cursor, query: str, limit: int, offset: int):
    cursor.execute(
        """
        SELECT DISTINCT ON (s.id)
            s.id,
            s.title,
            s.thumbnail_url,
            f.channel_username,
            sf.message_id
        FROM shows s
        JOIN show_files sf ON sf.show_id = s.id
        JOIN files f ON f.id = sf.file_id
        WHERE LOWER(s.title) = LOWER(%s)
          AND sf.message_id IS NOT NULL
        ORDER BY s.id, sf.message_id DESC
        LIMIT %s OFFSET %s
        """,
        (query, limit, offset),
    )
    return cursor.fetchall()


def search_prefix(cursor, query: str, limit: int, offset: int):
    cursor.execute(
        """
        SELECT DISTINCT ON (s.id)
            s.id,
            s.title,
            s.thumbnail_url,
            f.channel_username,
            sf.message_id
        FROM shows s
        JOIN show_files sf ON sf.show_id = s.id
        JOIN files f ON f.id = sf.file_id
        WHERE s.title ILIKE %s
          AND sf.message_id IS NOT NULL
        ORDER BY s.id, sf.message_id DESC
        LIMIT %s OFFSET %s
        """,
        (f"{query}%", limit, offset),
    )
    return cursor.fetchall()


def search_fuzzy(cursor, query: str, limit: int, offset: int):
    cursor.execute(
        """
        SELECT DISTINCT ON (s.id)
            s.id,
            s.title,
            s.thumbnail_url,
            f.channel_username,
            sf.message_id,
            similarity(s.title, %s) AS sim
        FROM shows s
        JOIN show_files sf ON sf.show_id = s.id
        JOIN files f ON f.id = sf.file_id
        WHERE sf.message_id IS NOT NULL
          AND s.title %% %s
        ORDER BY s.id, sim DESC, sf.message_id DESC
        LIMIT %s OFFSET %s
        """,
        (query, query, limit, offset),
    )
    return cursor.fetchall()


def search_shows_with_files(
    cursor, query: str, mode: str = "exact", limit: int = 10, offset: int = 0
):
    """
    Search shows beserta semua file terkait.

    mode:
        - "exact": exact match (case-insensitive)
        - "prefix": title starts with query (ILIKE)
        - "fuzzy": fuzzy search using pg_trgm (%% operator)
    """
    # Tentukan query SQL dasar
    sql = """
        SELECT
            s.id AS show_id,
            s.title AS show_title,
            s.thumbnail_url,
            f.id AS file_id,
            f.main_title,
            f.channel_username,
            f.message_id AS file_message_id,
            sf.id AS show_file_id,
            sf.message_id AS show_file_message_id
        FROM shows s
        JOIN show_files sf ON sf.show_id = s.id
        JOIN files f ON f.id = sf.file_id
        WHERE sf.message_id IS NOT NULL
    """
    params = []

    # Tambahkan kondisi pencarian
    if mode == "exact":
        sql += " AND LOWER(s.title) = LOWER(%s)"
        params.append(query)
    elif mode == "prefix":
        sql += " AND s.title ILIKE %s"
        params.append(f"{query}%")
    elif mode == "fuzzy":
        sql += " AND s.title %% %s"
        params.append(query)
    else:
        raise ValueError("mode harus 'exact', 'prefix', atau 'fuzzy'")

    # Order untuk ambil file terbaru per show
    if mode == "fuzzy":
        sql += " ORDER BY s.id, similarity(s.title, %s) DESC, sf.message_id DESC"
        params.append(query)
    else:
        sql += " ORDER BY s.id, sf.message_id DESC"

    # Limit & offset
    sql += " LIMIT %s OFFSET %s"
    params.extend([limit, offset])

    # Execute query
    cursor.execute(sql, params)
    rows = cursor.fetchall()

    # Grup per show
    shows = {}
    for row in rows:
        show_id = row["show_id"]
        if show_id not in shows:
            shows[show_id] = {
                "show_id": show_id,
                "title": row["show_title"],
                "thumbnail_url": row["thumbnail_url"],
                "files": [],
            }
        shows[show_id]["files"].append(
            {
                "file_id": row["file_id"],
                "main_title": row["main_title"],
                "channel_username": row["channel_username"],
                "file_message_id": row["file_message_id"],
                "show_file_id": row["show_file_id"],
                "show_file_message_id": row["show_file_message_id"],
            }
        )

    return list(shows.values())


def get_show_by_id(show_id: int) -> dict | None:
    with get_dict_cursor() as (cur, _):
        cur.execute(
            """
            SELECT
                id,
                title,
                thumbnail_url
            FROM shows
            WHERE id = %s
            LIMIT 1
            """,
            (show_id,),
        )
        row = cur.fetchone()

    return row if row else None
