from typing import Awaitable, Callable

from shared.utils.ui_session import clear_ui_lock  # ⬅️ khusus UI lock
from shared.utils.ui_session import (
    block_if_active,
    mark_ui_active,
)


async def with_ui_lock(user_id: int, coro_factory: Callable[[], Awaitable]):
    """
    Menjalankan coroutine dengan UI lock agar tiap user tidak bentrok.
    """
    if msg := block_if_active(user_id):
        return msg

    mark_ui_active(user_id)
    try:
        return await coro_factory()
    finally:
        clear_ui_lock(user_id)
