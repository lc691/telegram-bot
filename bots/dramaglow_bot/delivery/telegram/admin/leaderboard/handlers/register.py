from pyrogram import Client

from .commands import register_leaderboard_command_handler
from .callbacks import register_leaderboard_callback


def register_leaderboard(app: Client) -> None:
    """
    Register all VIP delivery handlers (commands, callbacks, cleanup).
    Order is important.
    """
    register_leaderboard_command_handler(app)
    register_leaderboard_callback(app)

    # optional, tapi sangat membantu
    # log.info("[VIP] handlers registered")
