from configs.logging_setup import log


async def get_channels_to_refresh(pool, bot_name: str):
    check_column_sql = """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = 'refresh_channels'
          AND column_name = 'bot_name'
    """
    column_exists = await pool.fetch(check_column_sql)

    if column_exists:
        query = """
            SELECT chat_id, username, invite_link
            FROM refresh_channels
            WHERE is_active = TRUE
              AND bot_name = $1
        """
        return await pool.fetch(query, bot_name)

    log.warning(
        "⚠️ Kolom 'bot_name' tidak ditemukan, query tanpa filter bot_name"
    )
    query = """
        SELECT chat_id, username, invite_link
        FROM refresh_channels
        WHERE is_active = TRUE
    """
    return await pool.fetch(query)
