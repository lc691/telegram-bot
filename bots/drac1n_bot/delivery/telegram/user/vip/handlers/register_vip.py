from pyrogram import Client

from .commands import register_vip_commands
from .callbacks import register_vip_callbacks

def register_vip(app: Client) -> None:
    """
    Register all VIP delivery handlers (commands, callbacks, cleanup).
    Order is important.
    """
    register_vip_commands(app)
    register_vip_callbacks(app)


    # optional, tapi sangat membantu
    # log.info("[VIP] handlers registered")
