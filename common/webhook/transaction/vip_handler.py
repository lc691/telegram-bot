# vip_transaction.py (FINAL - CLEAN, STEP CLEAR, MIN IO)

import uuid

from datetime import datetime, timezone

from dateutil import parser
from pyrogram.enums import ParseMode

from bots.drac1n_bot.services.affiliate.affiliate_commission import (
    process_affiliate_commission,
)
from common.bot_utils import resolve_bot
from common.messaging.log_proces import (
    log_action_start,
    log_activation_failure,
    log_activation_success,
    log_data_incomplete,
)
from common.messaging.notification_group import send_vip_group_announcement
from common.messaging.success_message import build_success_message
from common.utils.get_user import safe_get_user
from common.webhook.transaction.regular_handler import (
    insert_donation_log,
    process_regular_donation,
)
from common.webhook.vip.vip_validator import validate_promo_constraints
from config import POSTING_CHANNEL
from configs.logging_setup import log
from db.connect import get_db_cursor
from db.vip_users.vip_activation import safe_insert_vip_user
from db.vip_users.vip_db_utils import get_vip_package_info


# =====================================================================
# STEP FLOW:
# 1. Guard & logging
# 2. Paket validation
# 3. Promo constraint
# 4. Telegram user (optional)
# 5. DB activation (core)
# 6. Affiliate
# 7. DM user
# 8. Group announce
# 9. Donation log
# =====================================================================
async def process_vip_transaction(
    app,
    data: dict,
    message: str,
    source_bot: str,
    user_id: int,
    paket_raw: str,
    amount: int,
):

    # =====================================================
    # STEP 1 — Guard & initial log
    # =====================================================
    log_action_start(
        user_id=user_id,
        vip_user_id=user_id,
        paket=paket_raw,
        action="vip_webhook",
    )

    if not user_id or not paket_raw:
        log_data_incomplete(user_id, paket_raw)
        return "Data tidak lengkap", 400

    # =====================================================
    # STEP 2 — Paket validation
    # =====================================================
    paket_info = get_vip_package_info(paket_raw)
    if not paket_info:
        log_activation_failure(-1, user_id, paket_raw, "invalid_paket")
        return await process_regular_donation(app, data, message, source_bot)

    price = paket_info["price"]
    paket = paket_info["paket"]
    durasi_hari = paket_info["basic_days"] + paket_info.get("bonus_days", 0)

    if amount < price:
        log.info(
            "[VIP] Underpaid user=%s paket=%s paid=%s required=%s",
            user_id,
            paket,
            amount,
            price,
        )
        return (
            f"💸 Donasi kurang.\nHarga: Rp {price:,}\nDonasi: Rp {amount:,}",
            200,
        )

    log.info(
        "[VIP] Paket OK user=%s paket=%s durasi=%sh",
        user_id,
        paket,
        durasi_hari,
    )

    # =====================================================
    # STEP 3 — Promo constraint
    # =====================================================
    promo_violation = validate_promo_constraints(user_id, paket, paket_info)
    if promo_violation:
        log.info(
            "[VIP] Promo rejected user=%s paket=%s reason=%s",
            user_id,
            paket,
            promo_violation,
        )
        return promo_violation, 200

    # =====================================================
    # STEP 4 — Fetch Telegram user (BEST EFFORT)
    # =====================================================
    tg_user = None
    username = None

    try:
        tg_user = await safe_get_user(app, user_id)
        username = getattr(tg_user, "username", None)
    except Exception as e:
        log.debug("[VIP] TG fetch skipped user=%s err=%s", user_id, e)

    # =====================================================
    # STEP 5 — DB activation (CORE, SINGLE IO)
    # =====================================================
    batch_uuid = str(uuid.uuid4())

    insert_result = safe_insert_vip_user(
        user_id=user_id,
        username=username,
        paket=paket,
        durasi_hari=durasi_hari,
        basic_days=paket_info["basic_days"],
        bonus_days=paket_info.get("bonus_days", 0),
        admin_id=-1,
        keterangan="Webhook VIP activation",
        source_bot=source_bot,
        is_promo_once=paket_info.get("is_promo_once", False),
        batch_uuid=batch_uuid,
    )

    if not insert_result.get("success"):
        reason = insert_result.get("reason", "db_error")
        log_activation_failure(-1, user_id, paket, reason)
        return "Gagal aktivasi VIP", 500

    if insert_result.get("duplicate"):
        log.info(
            "[VIP] Duplicate ignored user=%s paket=%s",
            user_id,
            paket,
        )
        return "VIP already processed", 200

    log_activation_success(-1, user_id, insert_result, username)

    # =====================================================
    # STEP 6 — Affiliate commission
    # =====================================================
    if price > 0:
        await process_affiliate_commission(
            app,
            user_id=user_id,
            paket=paket,
            price=price,
            source_bot=source_bot,
        )
    else:
        log.info("[AFFILIATE] Skip (free/promo) user=%s", user_id)

    # =====================================================
    # STEP 7 — DM user (NON-CRITICAL)
    # =====================================================
    try:
        true_bot = resolve_bot(source_bot)

        with get_db_cursor() as (cursor, _):
            cursor.execute(
                "SELECT vip_start, vip_expired FROM users WHERE user_id=%s",
                (user_id,),
            )
            vip_start, vip_expired = cursor.fetchone()

        msg = build_success_message(
            tg_user,
            None,
            user_id,
            insert_result,
            source_bot,
            vip_start,
            vip_expired,
        )

        await true_bot.send_message(
            chat_id=user_id,
            text=msg,
            parse_mode=ParseMode.HTML,
        )

    except Exception as e:
        log.debug("[VIP] DM skipped user=%s err=%s", user_id, e)

    # =====================================================
    # STEP 8 — Group announcement (NON-CRITICAL)
    # =====================================================
    try:
        tx_time = (
            parser.isoparse(data["created_at"])
            if data.get("created_at")
            else datetime.now(timezone.utc)
        )

        await send_vip_group_announcement(
            app=true_bot,
            chat_id=POSTING_CHANNEL,
            username=tg_user.first_name if tg_user else "User",
            paket=paket,
            user_id=user_id,
            bonus_days=paket_info.get("bonus_days", 0),
            tx_time=tx_time,
            mode=insert_result["mode"],
            expired_at=insert_result.get("expired_at"),
            old_vip_end=insert_result.get("expired_lama"),
        )

    except Exception as e:
        log.warning(
            "[VIP] Group notify failed user=%s paket=%s err=%s",
            user_id,
            paket,
            e,
        )

    # =====================================================
    # STEP 9 — Donation log (FINAL IO)
    # =====================================================
    insert_donation_log(
        email=data.get("email", "unknown"),
        amount=amount,
        message=message,
        user_id=user_id,
        paket=paket,
        tipe="vip",
        source_bot=source_bot,
    )

    log.info(
        "[VIP] DONE user=%s paket=%s source=%s",
        user_id,
        paket,
        source_bot,
    )

    return "VIP activated", 200
