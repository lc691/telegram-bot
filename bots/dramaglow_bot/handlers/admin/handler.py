# bots/dramaglow_bot/callback/admin/handler.py

import re

from pyrogram import Client, filters
from pyrogram.types import CallbackQuery

from bots.dramaglow_bot.ui.dashboard import send_dashboard
from common.utils.admin_cache import admin_cache
from common.utils.admin_state_manager import AdminStateManager
from configs.logging_setup import log

from .routes import (
    admin_callback_routes,
    admin_regex_routes,
)


def register_admin_callback_handler(app: Client):
    @app.on_callback_query(filters.regex(r"^admin_"))
    async def admin_callback_handler(client: Client, callback_query: CallbackQuery):
        admin_id = callback_query.from_user.id
        data = callback_query.data
        state = AdminStateManager(admin_id)

        if not admin_cache.is_admin(admin_id):
            await callback_query.answer("⛔️ Anda bukan admin!", show_alert=True)
            log.warning(f"[ADMIN_CALLBACK] Akses ditolak: {admin_id}")
            return

        try:
            await callback_query.answer("⏳ Memproses permintaan...", show_alert=False)

            if data in admin_callback_routes:
                await admin_callback_routes[data](client, callback_query)
                log.info(f"[ADMIN_CALLBACK] Exact match: {data}")
                return

            for pattern, handler in admin_regex_routes.items():
                if re.match(pattern, data):
                    await handler(client, callback_query, state)
                    log.info(f"[ADMIN_CALLBACK] Regex match: {data}")
                    return

            log.warning(f"[ADMIN_CALLBACK] Tidak dikenali: {data}")
            await send_dashboard(source=callback_query, is_callback=True)

        except Exception as e:
            log.exception(f"[ADMIN_CALLBACK] Error: {data} → {e}")
            try:
                await callback_query.answer("❌ Terjadi kesalahan.", show_alert=True)
            except Exception:
                pass
