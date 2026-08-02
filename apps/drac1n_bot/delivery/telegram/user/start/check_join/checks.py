# modules/checks.py
from datetime import datetime, timezone
import asyncio
from pyrogram.enums import ChatMemberStatus
from pyrogram.errors import UserNotParticipant

from configs.logging_setup import log
from database.connection import get_db_cursor

from pyrogram.errors import (
    UserNotParticipant,
    FloodWait,
    ChatAdminRequired,
    ChannelInvalid,
)
from pyrogram.enums import ChatMemberStatus


async def is_user_in_channel(
    app,
    channel_username: str,
    user_id: int,
) -> bool:
    """
    Check if user is member of a channel.

    Returns:
        bool: True if joined, False if not.
    """

    try:
        member = await app.get_chat_member(channel_username, user_id)

        return member.status in (
            ChatMemberStatus.MEMBER,
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.OWNER,
            ChatMemberStatus.RESTRICTED,  # penting
        )

    except UserNotParticipant:
        return False

    except FloodWait as e:
        log.warning(
            "[JOIN_CHECK] FloodWait %ss channel=@%s user=%s",
            e.value,
            channel_username,
            user_id,
        )
        await asyncio.sleep(e.value)
        return await is_user_in_channel(app, channel_username, user_id)

    except ChatAdminRequired:
        log.error(
            "[JOIN_CHECK] bot not admin in @%s",
            channel_username,
        )
        # fail-open lebih aman daripada blok user
        return True

    except ChannelInvalid:
        log.error(
            "[JOIN_CHECK] invalid channel @%s",
            channel_username,
        )
        return True

    except Exception:
        log.exception(
            "[JOIN_CHECK] unexpected error channel=@%s user=%s",
            channel_username,
            user_id,
        )
        # fail-open supaya tidak lock semua user
        return True


async def log_channel_check(
    app,
    user_id: int,
    channel_username: str,
    is_joined: bool,
):
    """Simpan hasil pengecekan ke database (multi-bot safe)."""

    try:
        if not getattr(app.me, "username", None):
            await app.get_me()

        bot_username = app.me.username
        channel_username = channel_username.strip().lstrip("@")

        with get_db_cursor() as (cursor, conn):
            cursor.execute(
                """
                INSERT INTO user_channel_check
                (user_id, bot_username, channel_username, is_joined, checked_at)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (user_id, bot_username, channel_username)
                DO UPDATE
                SET is_joined = EXCLUDED.is_joined,
                    checked_at = EXCLUDED.checked_at
                """,
                (
                    user_id,
                    bot_username,
                    channel_username,
                    is_joined,
                    datetime.now(timezone.utc),
                ),
            )
            conn.commit()

    except Exception:
        log.exception(
            "[JOIN_LOG] failed user=%s channel=@%s",
            user_id,
            channel_username,
        )


async def check_required_channels(app, user_id: int, required_channels: list) -> list:
    not_joined = []

    tasks = [
        is_user_in_channel(app, username, user_id) for username in required_channels
    ]

    results = await asyncio.gather(*tasks, return_exceptions=True)

    for username, result in zip(required_channels, results):

        if isinstance(result, Exception):
            log.exception(
                "[JOIN_CHECK] error checking user=%s channel=@%s",
                user_id,
                username,
            )
            continue  # fail-open

        await log_channel_check(app, user_id, username, result)

        if not result:
            invite_link = f"https://t.me/{username}"
            not_joined.append((username, invite_link))

    return not_joined
