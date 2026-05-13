import asyncio
import os

from typing import Optional

from pyrogram import Client
from pyrogram.enums import ParseMode
from pyrogram.errors import FloodWait

from config import API_HASH, API_ID
from configs.logging_setup import log

from ..services.refresh_service import refresh_channels


async def create_bot(
    session_name: str,
    token: str,
    log_name: str,
    pool=None,
    retry_delay: int = 10,
) -> Optional[Client]:

    workdir = os.path.join("sessions", session_name)
    os.makedirs(workdir, exist_ok=True)

    while True:
        try:
            app = Client(
                name=session_name,
                api_id=API_ID,
                api_hash=API_HASH,
                bot_token=token,
                parse_mode=ParseMode.HTML,
                workdir=workdir,
                sleep_threshold=1,
            )

            await app.start()

            if pool:
                await refresh_channels(app, pool, session_name)

            return app

        except FloodWait as fw:
            await asyncio.sleep(fw.value + 5)

        except Exception as e:
            log.exception(f"❌ Start {log_name} gagal: {e}")
            await asyncio.sleep(retry_delay)
