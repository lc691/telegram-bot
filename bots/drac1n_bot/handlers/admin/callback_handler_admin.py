# bots/drac1n_bot/register/admin.py

from pyrogram import Client

from .grafik_donasi import register_grafik_donasi_handler
from .handler import register_admin_callback_handler


def register_admin_callback(app: Client):
    register_admin_callback_handler(app)
    register_grafik_donasi_handler(app)
