from pyrogram import Client

from ..handlers.admin.callback_handler_admin import register_admin_callback
from .callback_broadcast import register_broadcast_callback
from .callback_dashboard import register_dashboard_handler
from .callback_handler_common import register_common_callbacks
from .callback_handler_stats import register_stats_callback
from .callback_handler_vip import register_vip_callback
from .callback_nav_video import register_nav_video_callback
from .callback_feedback_handler import register_feedback_callback


# file: register_all_callbacks.py
def register_all_callbacks(app: Client):
    register_dashboard_handler(app)
    register_admin_callback(app)
    register_vip_callback(app)
    register_stats_callback(app)
    register_nav_video_callback(app)
    register_broadcast_callback(app)
    register_common_callbacks(app)
    register_feedback_callback(app)
