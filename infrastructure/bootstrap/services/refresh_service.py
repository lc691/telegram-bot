import asyncio

from pyrogram import Client
from pyrogram.errors import (
    FloodWait,
    InviteHashExpired,
    InviteHashInvalid,
    RPCError,
    UserAlreadyParticipant,
)

from configs.logging_setup import log

from ..repositories.channel_repo import get_channels_to_refresh


async def refresh_channels(client: Client, pool, bot_name: str):
    channels = await get_channels_to_refresh(pool, bot_name)

    for ch in channels:
        try:
            chat = None

            if ch["username"]:
                chat = await client.get_chat(ch["username"])

            elif ch["invite_link"]:
                try:
                    await client.join_chat(ch["invite_link"])
                except UserAlreadyParticipant:
                    pass
                except (InviteHashExpired, InviteHashInvalid):
                    continue

                chat = await client.get_chat(ch["invite_link"])

            elif ch["chat_id"]:
                chat = await client.get_chat(int(ch["chat_id"]))

            # if chat:
            #     log.info(f"✅ Refresh channel: {chat.title} ({chat.id})")

        except FloodWait as e:
            await asyncio.sleep(e.value)

        except RPCError as e:
            log.warning(f"⚠️ Gagal refresh {ch}: {e}")
