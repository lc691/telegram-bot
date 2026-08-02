from pyrogram import Client, filters
from pyrogram.enums import ParseMode
from pyrogram.errors import MessageNotModified
from pyrogram.types import CallbackQuery, InlineKeyboardMarkup

from apps.drac1n_bot.constants.vip_source import VipSource
from apps.drac1n_bot.keyboard.vip_tools import generate_vip_tools_markup
from shared.utils.callback_helpers import safe_answer
from shared.utils.fsm_helpers import validate_no_conflict
from shared.utils.vip_state_manager import VipStateManager
from configs.logging_setup import log


def register_vip_menu_handler(app: Client):
    @app.on_callback_query(filters.regex(r"^vip_tools:(drac1n|utbk)$"))
    async def handle_vip_menu_detail(client: Client, callback_query: CallbackQuery):
        user = callback_query.from_user
        user_id = user.id
        is_answered = False

        try:
            _, source_bot = callback_query.data.split(":")
            if source_bot not in VipSource._value2member_map_:
                await safe_answer(
                    callback_query, "❌ Sumber bot tidak dikenali", show_alert=True
                )
                return

            source = VipSource(source_bot)
            state = VipStateManager(user_id, source_bot=source_bot)

            if not await validate_no_conflict(user_id, state, callback_query):
                return

            state.set_temp("source_bot", source_bot)
            await safe_answer(callback_query, "✅ Masuk ke menu VIP tools")
            is_answered = True

            log.info(
                f"[VIP Menu] User @{user.username or user_id} membuka menu VIP Tools untuk '{source_bot}'"
            )

            markup = generate_vip_tools_markup(source_bot) or InlineKeyboardMarkup([])
            try:
                await callback_query.message.edit_text(
                    f"🌟 <b>VIP Tools - {source.name.capitalize()}</b>",
                    reply_markup=markup,
                    parse_mode=ParseMode.HTML,
                )
            except MessageNotModified:
                log.warning("[VIP Menu] Gagal mengedit pesan menu VIP.")

        except Exception as e:
            log.error(
                f"[handle_vip_menu_detail] Gagal membuka menu VIP: {e}", exc_info=True
            )
            if not is_answered:
                await safe_answer(
                    callback_query, "❌ Gagal membuka menu VIP", show_alert=True
                )
