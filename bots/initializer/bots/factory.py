from typing import Optional
from pyrogram import Client

from config import (
    BOT_TOKEN,
    BOT_TOKEN_GLOW,
    BOT_TOKEN_CARI,
    BOT_TOKEN_KELOLA,
    BOT_TOKEN_UTBK,
)

from .bot_creator import create_bot


async def create_app(pool) -> Optional[Client]:
    return await create_bot("drac1n_bot", BOT_TOKEN, "drac1n_bot", pool)


async def create_app_glow(pool) -> Optional[Client]:
    return await create_bot("dramaglow_bot", BOT_TOKEN_GLOW, "dramaglow_bot", pool)


async def create_utbk_app(pool) -> Optional[Client]:
    return await create_bot("utbkvip_bot", BOT_TOKEN_UTBK, "utbkvip_bot", pool)


async def create_dcst_app(pool) -> Optional[Client]:
    return await create_bot("kelolain_bot", BOT_TOKEN_KELOLA, "kelolain_bot", pool)


async def create_caridrama_app(pool) -> Optional[Client]:
    return await create_bot("caridrama_bot", BOT_TOKEN_CARI, "caridrama_bot", pool)
