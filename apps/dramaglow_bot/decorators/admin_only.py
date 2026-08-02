from functools import wraps

from pyrogram.types import Message

from shared.utils.admin_cache import admin_cache


def admin_only():
    def decorator(func):
        @wraps(func)
        async def wrapper(client, message: Message, *args, **kwargs):
            try:
                user_id = message.from_user.id
                is_admin = await admin_cache.is_admin_async(user_id)  # 🔁 Pakai async

                if not is_admin:
                    await message.reply_text(
                        "⛔️ Akses ditolak. Fitur ini hanya untuk admin."
                    )
                    return

                return await func(client, message, *args, **kwargs)

            except Exception as e:
                await message.reply_text(
                    "⚠️ Terjadi kesalahan saat memverifikasi admin."
                )
                raise e

        return wrapper

    return decorator
