from functools import wraps

from pyrogram.types import Message

from shared.utils.admin_cache import admin_cache


from functools import wraps
from pyrogram.types import Message
from shared.utils.admin_cache import admin_cache


def admin_only():
    def decorator(func):
        @wraps(func)
        async def wrapper(client, message: Message, *args, **kwargs):
            try:
                user = message.from_user
                if not user:
                    return

                user_id = user.id

                # ✅ TANPA await
                is_admin = admin_cache.is_admin(user_id)

                if not is_admin:
                    await message.reply_text(
                        "⛔️ Akses ditolak. Fitur ini hanya untuk admin."
                    )
                    return

                return await func(client, message, *args, **kwargs)

            except Exception:
                await message.reply_text(
                    "⚠️ Terjadi kesalahan saat memverifikasi admin."
                )
                raise  # preserve traceback

        return wrapper

    return decorator
