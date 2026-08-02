from asyncio import to_thread
from datetime import datetime, timezone

from pyrogram import Client
from pyrogram.enums import ParseMode
from pyrogram.types import CallbackQuery

from infrastructure.telegram.bots_registry import get_bot
from shared.bot_utils import get_clean_bot_key
from shared.messaging.log_proces import (
    log_activation_failure,
    log_activation_success,
)
from shared.messaging.success_message import build_success_message
from shared.utils.get_user import safe_get_user
from shared.utils.vip_state_manager import VipStateManager
from configs.logging_setup import log
from database.connection import get_db_cursor
from database.vip_users.vip_activation import safe_insert_vip_user


async def process_vip_activation(
    app: Client,
    callback: CallbackQuery,
    admin_id: int,
    user_id: int,
    paket: str,
    state: VipStateManager,
    force_override: bool = False,
):
    source_bot = get_clean_bot_key(state.get_temp("source_bot") or "drac1n")
    today_str = datetime.now(timezone.utc).date().isoformat()
    true_bot = get_bot(source_bot) or app

    if state.get_temp("is_processing"):
        await callback.answer("⏳ Masih memproses aktivasi sebelumnya...")
        return

    state.set_temp("is_processing", True)

    try:
        if not force_override and _is_duplicate_activation(user_id, paket, today_str):
            log.info(
                f"[VIP_ACTIVATION] ⚠️ Duplikat aktivasi dicegah untuk {user_id} paket={paket}"
            )
            await callback.message.edit_text(
                "⚠️ Aktivasi ini sudah dicatat dan sedang diproses. Harap tunggu notifikasi."
            )
            await callback.answer(
                "⚠️ Aktivasi sudah tercatat sebelumnya.", show_alert=True
            )
            return

        if _is_already_vip(user_id, source_bot) and not force_override:
            log.warning(
                f"[VIP_ACTIVATION] ❌ User {user_id} sudah VIP di bot={source_bot}."
            )
            await callback.message.edit_text("⚠️ User sudah menjadi VIP sebelumnya.")
            await callback.answer("User sudah aktif sebagai VIP.", show_alert=True)
            return

        try:
            result = await to_thread(
                safe_insert_vip_user,
                user_id,
                paket,
                admin_id,
                source_bot=source_bot,
                keterangan="Aktivasi manual oleh admin",
            )
        except Exception as db_err:
            raise RuntimeError(f"Gagal aktivasi di database: {db_err}")

        if not result.get("success"):
            raise RuntimeError("Aktivasi VIP gagal.")

        result["paket"] = paket
        await _notify_activation_success(
            app=true_bot,
            callback=callback,
            admin_id=admin_id,
            user_id=user_id,
            result=result,
            source_bot=source_bot,
        )

    except Exception as e:
        await _handle_activation_failure(callback, user_id, e)

    finally:
        state.clear_temp("is_processing")


def _is_duplicate_activation(user_id: int, paket: str, today_str: str) -> bool:
    with get_db_cursor() as (cursor, _):
        cursor.execute(
            """
            SELECT 1 FROM vip_logs
            WHERE target_user_id = %s
              AND paket = %s
              AND is_notified = FALSE
              AND timestamp_date = %s
            LIMIT 1
            """,
            (user_id, paket, today_str),
        )
        return cursor.fetchone() is not None


def _is_already_vip(user_id: int, source_bot: str) -> bool:
    with get_db_cursor() as (cursor, _):
        cursor.execute(
            """
            SELECT 1 FROM vip_users
            WHERE user_id = %s AND source_bot = %s
            LIMIT 1
            """,
            (user_id, source_bot),
        )
        return cursor.fetchone() is not None


async def _notify_activation_success(
    app: Client,
    callback: CallbackQuery,
    admin_id: int,
    user_id: int,
    result: dict,
    source_bot: str,
):
    user = await safe_get_user(app, user_id) or {
        "id": user_id,
        "first_name": "-",
    }
    admin_user = await safe_get_user(app, admin_id) or {
        "id": admin_id,
        "first_name": "-",
    }

    msg_text = build_success_message(user, admin_user, user_id, result, source_bot)

    try:
        await callback.message.edit_text(msg_text, parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        log.warning(f"[VIP_ACTIVATION] Gagal edit pesan admin: {e}", exc_info=True)
        await callback.answer("⚠️ Gagal mengedit pesan.", show_alert=True)

    try:
        await app.send_message(
            chat_id=user_id,
            text=msg_text,
            parse_mode=ParseMode.HTML,
        )
    except Exception as send_err:
        log.warning(
            f"[VIP_ACTIVATION] ⚠️ Gagal kirim notifikasi ke user_id={user_id}: {send_err}"
        )

    log_activation_success(admin_id, user_id, result)
    log.info(
        f"[VIP_ACTIVATION] ✅ admin_id={admin_id} activated VIP user_id={user_id} paket={result.get('paket')} via {source_bot}"
    )


async def _handle_activation_failure(
    callback: CallbackQuery, user_id: int, e: Exception
):
    try:
        await callback.message.edit_text("⚠️ Gagal menghubungi basis data.")
    except Exception:
        await callback.answer("⚠️ Gagal menghubungi basis data.", show_alert=True)

    log_activation_failure(user_id, e)
    log.error(
        f"[VIP_ACTIVATION] ❌ Error saat aktivasi user_id={user_id}: {e}",
        exc_info=True,
    )
