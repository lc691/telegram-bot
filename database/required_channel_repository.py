from datetime import datetime

from database.connection import get_db_cursor


async def load_required_channels(app):
    if not getattr(app.me, "username", None):
        await app.get_me()

    bot_username = app.me.username

    with get_db_cursor() as (cursor, conn):
        cursor.execute(
            """
            SELECT username
            FROM required_channels
            WHERE is_active = TRUE
            AND bot_username = %s
            ORDER BY added_at DESC
            """,
            (bot_username,),
        )
        return [row[0] for row in cursor.fetchall()]


async def save_required_channel(app, username, added_by):
    if not getattr(app.me, "username", None):
        await app.get_me()

    bot_username = app.me.username
    username = username.strip().lstrip("@")

    with get_db_cursor() as (cursor, conn):
        cursor.execute(
            """
            INSERT INTO required_channels
            (bot_username, username, added_by)
            VALUES (%s, %s, %s)
            ON CONFLICT (bot_username, username) DO NOTHING
            """,
            (bot_username, username, added_by),
        )
        conn.commit()


async def delete_required_channel(app, username):
    if not getattr(app.me, "username", None):
        await app.get_me()

    bot_username = app.me.username
    username = username.strip().lstrip("@")

    with get_db_cursor() as (cursor, conn):
        cursor.execute(
            """
            DELETE FROM required_channels
            WHERE bot_username = %s
            AND username = %s
            """,
            (bot_username, username),
        )
        conn.commit()
