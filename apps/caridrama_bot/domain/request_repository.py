def insert_show_request(
    cursor,
    *,
    user_id: int,
    show_id: int,
    username: str | None,
    fullname: str | None,
) -> bool:
    """
    Insert request drama ke DB.
    Return:
        True  -> request baru
        False -> request sudah ada
    """

    cursor.execute(
        """
        INSERT INTO show_requests (
            user_id,
            show_id,
            username,
            fullname,
            status,
            created_at
        )
        VALUES (%s, %s, %s, %s, 'pending', NOW())
        ON CONFLICT (user_id, show_id)
        DO NOTHING
        """,
        (user_id, show_id, username, fullname),
    )

    return cursor.rowcount > 0
