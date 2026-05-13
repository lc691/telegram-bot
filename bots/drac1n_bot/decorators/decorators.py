from functools import wraps

from pyrogram.types import CallbackQuery, Message

from common.utils.admin_cache import admin_cache
from configs.logging_setup import log


def log_admin_activity(action_desc="melakukan aksi"):
    def decorator(func):
        @wraps(func)
        async def wrapper(client, update, *args, **kwargs):
            user_id = (
                update.from_user.id
                if isinstance(update, (Message, CallbackQuery))
                else None
            )
            username = update.from_user.username if update.from_user else "unknown"

            if admin_cache.is_admin(user_id):
                log.info(f"🛡️ Admin @{username} ({user_id}) {action_desc}")
            return await func(client, update, *args, **kwargs)

        return wrapper

    return decorator
