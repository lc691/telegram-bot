from pyrogram import Client

from ..callback.vip.vip_callback_router import register_vip_router
from ..callback.vip.vip_menu_handler import register_vip_menu_handler


def register_vip_callback(app: Client):
    register_vip_menu_handler(app)
    register_vip_router(app)
