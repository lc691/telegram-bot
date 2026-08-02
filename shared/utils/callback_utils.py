from pyrogram.types import CallbackQuery
from pyrogram.errors import RPCError

from configs.logging_setup import log
from .menu_utils import edit_menu


async def handle_menu_callback(
    callback: CallbackQuery,
    text: str,
    markup=None,
):
    """
    Handler standar callback menu.
    """

    # 1. ACK (hilangkan loading)
    try:
        await callback.answer()
    except RPCError as e:
        log.warning("[handle_menu_callback] answer gagal: %s", e)

    # 2. EDIT MENU
    return await edit_menu(
        event=callback,
        text=text,
        markup=markup,
    )
