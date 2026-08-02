from pyrogram import Client
from pyrogram.enums import ParseMode
from pyrogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from apps.drac1n_bot.keyboard.vip_tools import generate_vip_tools_markup
from shared.bot_utils import get_table_name
from shared.utils.callback_helpers import safe_answer
from shared.utils.escape_markdown import escape_md
from shared.utils.fsm_helpers import validate_no_conflict
from shared.utils.vip_state_manager import VipStateManager
from configs.logging_setup import log
from database.vip_users.vip_utils import deactivate_expired_vips

CONFIRMATION_TEXT = "⚠️ Yakin ingin reset semua user VIP yang sudah expired?"


async def vip_reset_all_start(client: Client, callback_query: CallbackQuery):
    admin_id = callback_query.from_user.id
    state = VipStateManager(admin_id)

    source_bot = state.get_temp("source_bot") or getattr(client, "bot_name", "drac1n")
    state.set_temp("source_bot", source_bot)

    if not await validate_no_conflict(admin_id, state, callback_query):
        return

    try:
        state.set_vip_reset_step("waiting_bulk_confirmation")

        if callback_query.message.text != CONFIRMATION_TEXT:
            await _send_confirmation_prompt(callback_query, source_bot)
            log.info(
                "[VIP RESET ALL] Prompt ditampilkan oleh admin_id=%s | bot=%s",
                admin_id,
                source_bot,
            )
        else:
            await safe_answer(callback_query, "✅ Prompt sudah ditampilkan.")

    except Exception as e:
        log.error("[VIP RESET ALL] ❌ Gagal tampilkan konfirmasi: %s", e, exc_info=True)
        try:
            await callback_query.message.edit_text("❌ Gagal menampilkan konfirmasi.")
        except Exception as e2:
            log.error("[VIP RESET ALL] ❌ Gagal fallback edit: %s", e2, exc_info=True)


async def handle_vip_reset_all_step(client: Client, callback_query: CallbackQuery):
    admin_id = callback_query.from_user.id
    state = VipStateManager(admin_id)

    if state.get_vip_reset_step() != "waiting_bulk_confirmation":
        await safe_answer(
            callback_query, "⚠️ Aksi sudah tidak berlaku.", show_alert=True
        )
        return

    data = callback_query.data
    source_bot = (
        data.split(":")[1] if ":" in data else getattr(client, "bot_name", "drac1n")
    )

    try:
        table = get_table_name(source_bot)
        if not table:
            await callback_query.message.edit_text(
                f"⚠️ Bot <code>{escape_md(source_bot)}</code> tidak memiliki tabel user.",
                parse_mode=ParseMode.HTML,
            )
            return

        count = deactivate_expired_vips(source_bot=source_bot, table=table)
        await _execute_bulk_reset(callback_query, count, source_bot)

        log.info(
            "[VIP RESET ALL] ✅ %s VIP expired dinonaktifkan oleh admin_id=%s | bot=%s",
            count,
            admin_id,
            source_bot,
        )

    except Exception as e:
        log.error("[VIP RESET ALL] ❌ Gagal reset semua VIP: %s", e, exc_info=True)
        try:
            await callback_query.message.edit_text("❌ Gagal melakukan reset massal.")
        except Exception as e2:
            log.error("[VIP RESET ALL] ❌ Fallback gagal: %s", e2, exc_info=True)
    finally:
        try:
            state.clear()
        except Exception as e:
            log.error(
                "[VIP RESET ALL] ❌ Gagal clear state admin_id=%s: %s",
                admin_id,
                e,
                exc_info=True,
            )


# ────────────── Helper Functions ──────────────


async def _send_confirmation_prompt(callback_query: CallbackQuery, source_bot: str):
    try:
        await callback_query.message.edit_text(
            CONFIRMATION_TEXT,
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "✅ Ya",
                            callback_data=f"vip_reset_all_confirm_yes:{source_bot}",
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "❌ Batal", callback_data=f"vip_tools:{source_bot}"
                        )
                    ],
                ]
            ),
        )
        await safe_answer(callback_query)
    except Exception as e:
        log.error(
            "[VIP RESET ALL] ❌ Gagal kirim prompt konfirmasi: %s", e, exc_info=True
        )


async def _execute_bulk_reset(
    callback_query: CallbackQuery, count: int, source_bot: str
):
    try:
        result_text = f"✅ Selesai! `{count}` user VIP yang expired telah direset."

        await callback_query.message.edit_text(
            result_text, parse_mode=ParseMode.MARKDOWN
        )

        markup = generate_vip_tools_markup(source_bot)
        if markup:
            await callback_query.message.edit_text(
                f"🌟 <b>VIP Tools - {escape_md(source_bot)}</b>",
                reply_markup=markup,
                parse_mode=ParseMode.HTML,
            )
        else:
            await callback_query.message.edit_text(
                "ℹ️ Reset selesai, tapi tidak bisa tampilkan menu kembali.",
                parse_mode=ParseMode.HTML,
            )

    except Exception as e:
        log.error(
            "[VIP RESET ALL] ❌ Gagal kembali ke menu VIP Tools: %s", e, exc_info=True
        )
        await callback_query.answer(
            "⚠️ Reset berhasil, tapi gagal kembali ke menu.", show_alert=True
        )
