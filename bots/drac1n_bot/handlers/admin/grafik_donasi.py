# bots/drac1n_bot/handlers/admin/commands/grafik_donasi.py

from pyrogram import Client, filters

from bots.drac1n_bot.handlers.vip.vip_stats import send_donation_chart
from config import ADMIN_IDS


def register_grafik_donasi_handler(app: Client):
    @app.on_message(filters.command("grafik_donasi") & filters.user(ADMIN_IDS))
    async def grafik_donasi_handler(client, message):
        await send_donation_chart(client, message.chat.id)
