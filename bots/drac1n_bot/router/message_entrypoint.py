from pyrogram.types import Message
from configs.logging_setup import log

from common.utils.admin_cache import admin_cache
from common.utils.admin_state_manager import AdminStateManager
from common.utils.state_helper import cancel_all_states, should_cancel_state_on_command
from common.utils.event_tracer import EventTracer

from db.chanel_management import discard_user, is_user_adding
from bots.drac1n_bot.delivery.telegram.user.services.channel_repository import save_required_channel
from bots.drac1n_bot.ui.dashboard import send_dashboard

from .admin_text_router import handle_admin_text
from .request_text_handler import handle_request_text
from .search_text_handler import handle_search_text
from .vip_text_router import handle_vip_text

async def message_entrypoint(client, message):
    user = message.from_user
    if not user:
        return

    if user.is_bot:
        return

    user_id = user.id
    text = message.text.strip() if message.text else ""

    tracer = EventTracer(user_id)
    tracer.entry(text)

    try:
        if is_user_adding(user_id):
            tracer.handler("channel_add_flow")
            save_required_channel(text, user.username or str(user_id))
            tracer.result("CHANNEL_ADDED")
            return await send_dashboard(source=message, is_callback=False)

        is_admin = admin_cache.is_admin(user_id)

        if should_cancel_state_on_command(text):
            tracer.event("CANCEL_FLOW")
            cancel_all_states(user_id)
            tracer.result("CANCELLED")
            return await send_dashboard(source=message, is_callback=False)

        tracer.handler("admin_text")
        if await handle_admin_text(client, message, is_admin):
            tracer.result("ADMIN_HANDLED")
            return

        tracer.handler("vip_text")
        if await handle_vip_text(client, message, is_admin):
            tracer.result("VIP_HANDLED")
            return

        tracer.handler("request_text")
        if await handle_request_text(client, message):
            tracer.result("REQUEST_HANDLED")
            return

        tracer.handler("search_text")
        if await handle_search_text(client, message):
            tracer.result("SEARCH_HANDLED")
            return

        admin_state = AdminStateManager(user_id)
        tracer.state(str(admin_state.current_step()))

        if admin_state.has_active_step():
            tracer.result("STATE_BLOCKED")
            return

        tracer.handler("autocomplete")
        if await handle_autocomplete_source(client, message):
            tracer.result("AUTOCOMPLETE_HANDLED")
            return

        tracer.result("NO_ACTION")

    except Exception as e:
        tracer.error(str(e))
        await message.reply_text("⚠️ Terjadi kesalahan.")