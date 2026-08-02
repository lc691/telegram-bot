from pyrogram import Client
from pyrogram.types import CallbackQuery

from configs.logging_setup import log
from ..services.service_donasi import handle_donasi_metode


async def process_donasi_callback(client: Client, callback: CallbackQuery):
    log.info(
        "[DONASI] Callback method=%s user_id=%s",
        callback.data,
        callback.from_user.id if callback.from_user else None,
    )

    await handle_donasi_metode(client, callback)
