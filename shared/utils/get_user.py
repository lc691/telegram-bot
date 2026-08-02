from types import SimpleNamespace

from pyrogram import Client

from configs.logging_setup import log


async def safe_get_user(app: Client, user_id: int):
    try:
        return await app.get_users(user_id)
    except Exception as e:
        log.warning(f"[VIP_CONFIRM] Tidak bisa ambil info user_id={user_id}: {e}")
        return SimpleNamespace(username="-", first_name="-", id=user_id)
