from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, Message

from bots.drac1n_bot.decorators.admin_only import admin_only
from bots.drac1n_bot.ui.dashboard import send_dashboard
from bots.drac1n_bot.ui.menu_handler import handle_dynamic_menu
from common.utils.state_helper import cancel_all_states
from common.utils.state_manager import search_prompts
from configs.logging_setup import log

# Regex untuk semua menu utama (tanpa data kosong)
MENU_REGEX = r"^(admin_tools_menu|vip_tools_menu|channel_menu|dashboard|request_menu|show_stats|refresh_dashboard|close)$"


def register_dashboard_handler(app: Client):
    """Registrasi command & callback handler untuk dashboard."""

    @app.on_message(filters.command("dashboard"))
    @admin_only()
    async def dashboard_command(client: Client, message: Message):
        """Handler command /dashboard dari admin."""
        try:
            cancel_all_states(message.from_user.id)
            await send_dashboard(source=message, is_callback=False)
        except Exception as e:
            log.error(
                "[dashboard_command] ❌ Gagal kirim dashboard: %s", e, exc_info=True
            )
            await message.reply_text("❌ Terjadi kesalahan saat membuka dashboard.")

    @app.on_callback_query(filters.regex(MENU_REGEX))
    async def all_callback_handler(client: Client, callback_query: CallbackQuery):
        """Handler semua tombol menu di dashboard."""
        data = callback_query.data
        user_id = callback_query.from_user.id

        try:
            cancel_all_states(user_id)

            if data == "refresh_dashboard":
                await send_dashboard(source=callback_query, is_callback=True)

            elif data == "close":
                search_prompts.pop(user_id, None)
                await callback_query.message.delete()
                await callback_query.answer("❌ Panel ditutup. Semua sesi dibatalkan.")

            else:
                await handle_dynamic_menu(callback_query)

        except Exception as e:
            log.error(
                "[all_callback_handler] ❌ Gagal proses callback: %s", e, exc_info=True
            )
            await callback_query.answer(
                "❌ Terjadi kesalahan saat memproses.", show_alert=True
            )
