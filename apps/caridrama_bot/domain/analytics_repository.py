def track_query_miss(
    cursor,
    *,
    query: str,
    user_id: int,
    source: str,
):
    """
    Simpan atau update analytics query miss.
    """
    cursor.execute(
        """
        INSERT INTO search_query_miss (query, user_id, source, hit_count)
        VALUES (%s, %s, %s, 1)
        ON CONFLICT (query, source)
        DO UPDATE SET
            hit_count = search_query_miss.hit_count + 1,
            last_seen = NOW()
        """,
        (query.lower(), user_id, source),
    )
