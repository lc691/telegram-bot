from pyrogram import Client

from bots.drac1n_bot.delivery.telegram.admin.leaderboard.handlers.commands import register_leaderboard_command_handler
from bots.drac1n_bot.delivery.telegram.admin.leaderboard.handlers.callbacks import register_leaderboard_callback


def register_leaderboard(app: Client) -> None:
    """
    Register all VIP delivery handlers (commands, callbacks, cleanup).
    Order is important.
    """
    register_leaderboard_command_handler(app)
    register_leaderboard_callback(app)

    # optional, tapi sangat membantu
    # log.info("[VIP] handlers registered")
