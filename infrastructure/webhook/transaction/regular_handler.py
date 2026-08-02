# =====================[ PROSES DONASI REGULER - FINAL SAFE ]=====================

import re
from asyncio import create_task
from datetime import datetime
from typing import Tuple
from zoneinfo import ZoneInfo

from pyrogram import Client

from shared.bot_utils import get_clean_bot_key
from shared.messaging.email_responder import send_email_reply_async
from shared.messaging.notification_regular_group import send_donation_group_announcement
from shared.messaging.regular.normalize_donation_message import normalize_donation_message
from infrastructure.webhook.utils.trakteer_transactions import calculate_amount
from config import POSTING_CHANNEL, SPECIAL_DONORS
from configs.logging_setup import log
from database.vip_users.vip_log_donation import insert_donation_log


async def process_regular_donation(
    app: Client,
    data: dict,
    message: str,
    fallback_bot: str = "drac1n",
) -> Tuple[str, int]:

    tx_id = data.get("transaction_id", "<no-txid>")
    log.info("[DONATION] ▶ start tx_id=%s", tx_id)

    # =========================
    # STEP 1 — Amount
    # =========================
    try:
        amount, amount_source = calculate_amount(data)
    except Exception:
        log.exception("[DONATION] amount calculation failed tx_id=%s", tx_id)
        return "Internal error", 500

    if amount <= 0:
        log.warning("[DONATION] invalid amount tx_id=%s", tx_id)
        return "Jumlah donasi tidak valid", 400

    # =========================
    # STEP 2 — Identity
    # =========================
    raw_supporter_name = (data.get("supporter_name") or "").strip()
    raw_email = (data.get("email") or "").strip()

    if not raw_email and raw_supporter_name:
        raw_email = f"{raw_supporter_name}@trakteer"

    email = raw_email if re.match(r"[^@]+@[^@]+\.[^@]+", raw_email) else "unknown"

    donor_name = (
        raw_supporter_name
        or (email.split("@")[0] if email != "unknown" else "User")
    )

    # =========================
    # STEP 3 — Bot source
    # =========================
    source_bot = fallback_bot
    match = re.search(r"@(\w+)", message or "")
    if match:
        clean_bot = get_clean_bot_key(match.group(1).lower())
        if clean_bot:
            source_bot = clean_bot

    # =========================
    # STEP 4 — Log DB (safe)
    # =========================
    try:
        insert_donation_log(
            email=email,
            amount=amount,
            message=message,
            user_id=data.get("user_id"),
            paket=None,
            tipe="donasi",
            source_bot=source_bot,
        )
    except Exception:
        log.warning("[DONATION] log insert failed tx_id=%s", tx_id, exc_info=True)

    # =========================
    # STEP 5 — Special donor (FIXED)
    # =========================
    if email != "unknown" and isinstance(SPECIAL_DONORS, dict):
        special_msg = SPECIAL_DONORS.get(email)

        if special_msg:
            try:
                create_task(send_email_reply_async(email, special_msg))
                log.debug(
                    "[DONATION] special email queued tx_id=%s email=%s",
                    tx_id,
                    email,
                )
            except Exception:
                log.warning(
                    "[DONATION] special email failed tx_id=%s",
                    tx_id,
                    exc_info=True,
                )

    # =========================
    # STEP 6 — Normalize message
    # =========================
    donation_message, note_empty = normalize_donation_message(message)

    # =========================
    # STEP 7 — Time
    # =========================
    try:
        created_at = data.get("created_at")
        tx_time = (
            datetime.fromisoformat(created_at).astimezone(ZoneInfo("Asia/Jakarta"))
            if created_at
            else datetime.now(ZoneInfo("Asia/Jakarta"))
        )
    except Exception:
        tx_time = datetime.now(ZoneInfo("Asia/Jakarta"))

    # =========================
    # STEP 8 — Send notification
    # =========================
    await send_donation_group_announcement(
        app=app,
        chat_id=POSTING_CHANNEL,
        username=donor_name,
        paket=str(amount),
        message_text=donation_message,
        note_empty=note_empty,
        email=email,
        tx_time=tx_time,
        user_id=data.get("user_id"),
    )

    log.info(
        "[DONATION] ✅ completed tx_id=%s amount=%s bot=%s",
        tx_id,
        amount,
        source_bot,
    )

    return "Donasi dicatat", 200
