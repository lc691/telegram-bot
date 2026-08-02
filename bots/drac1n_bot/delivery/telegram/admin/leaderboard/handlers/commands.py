from pyrogram import Client, filters
from pyrogram.types import Message

from bots.drac1n_bot.delivery.telegram.admin.leaderboard.usecases.leaderboard_flow import (
    show_leaderboard
)

from bots.drac1n_bot.delivery.telegram.admin.leaderboard.utils.timezone import (
    today_wib
)

GROUP = 5


def register_leaderboard_command_handler(app: Client):
    @app.on_message(filters.command(["leaderboard", "topvip"]), group=GROUP)
    async def leaderboard_cmd(client: Client, message: Message):
        """
        Entry point leaderboard via command.

        Default:
        - period : daily
        - page   : 1
        - date   : hari ini (WIB)
        """

        await show_leaderboard(
            client=client,
            event=message,
            period="daily",
            page=1,
            date=today_wib().isoformat(),
        )
