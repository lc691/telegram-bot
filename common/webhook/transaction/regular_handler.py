# =====================[ PROSES DONASI REGULER - FINAL ]=====================

import re

from asyncio import create_task
from datetime import datetime
from typing import Tuple
from zoneinfo import ZoneInfo

from pyrogram import Client

from common.bot_utils import get_clean_bot_key
from common.messaging.email_responder import send_email_reply_async
from common.messaging.notification_regular_group import send_donation_group_announcement
from common.messaging.regular.normalize_donation_message import (
    normalize_donation_message,
)
from common.webhook.utils.trakteer_transactions import calculate_amount
from config import POSTING_CHANNEL, SPECIAL_DONORS
from configs.logging_setup import log
from db.vip_users.vip_log_donation import insert_donation_log


async def process_regular_donation(
    app: Client,
    data: dict,
    message: str,
    fallback_bot: str = "drac1n",
) -> Tuple[str, int]:
    """
    Proses donasi reguler.
    Clean logging, fail-safe, production ready.
    """

    tx_id = data.get("transaction_id", "<no-txid>")
    log.info("[DONATION] ▶ start tx_id=%s", tx_id)

    # =====================================================
    # STEP 1 — Calculate amount
    # =====================================================
    try:
        amount, amount_source = calculate_amount(data)
    except Exception:
        log.exception("[DONATION] ❌ amount calculation failed tx_id=%s", tx_id)
        return "Internal error", 500

    if amount <= 0:
        log.warning(
            "[DONATION] ❌ invalid amount tx_id=%s amount=%s",
            tx_id,
            amount,
        )
        return "Jumlah donasi tidak valid", 400

    log.debug(
        "[DONATION] amount calculated tx_id=%s amount=%s source=%s",
        tx_id,
        amount,
        amount_source,
    )

    # =====================================================
    # STEP 2 — Extract supporter & email
    # =====================================================
    raw_supporter_name = (data.get("supporter_name") or "").strip()
    raw_email = (data.get("email") or "").strip()

    if not raw_email and raw_supporter_name:
        raw_email = f"{raw_supporter_name}@trakteer"

    if raw_email and re.match(r"[^@]+@[^@]+\.[^@]+", raw_email):
        email = raw_email
    else:
        email = "unknown"

    # =====================================================
    # STEP 3 — Resolve donor display name
    # =====================================================
    if raw_supporter_name:
        donor_name = raw_supporter_name
    elif email != "unknown":
        donor_name = email.split("@", 1)[0]
    else:
        donor_name = "User"

    # =====================================================
    # STEP 4 — Resolve source bot
    # =====================================================
    source_bot = fallback_bot
    match = re.search(r"@(\w+)", message or "")
    if match:
        clean_bot = get_clean_bot_key(match.group(1).lower())
        if clean_bot:
            source_bot = clean_bot

    log.debug(
        "[DONATION] parsed tx_id=%s donor=%s email=%s bot=%s",
        tx_id,
        donor_name,
        email,
        source_bot,
    )

    # =====================================================
    # STEP 5 — Save donation log (BEST EFFORT)
    # =====================================================
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
        log.warning(
            "[DONATION] log insert failed tx_id=%s",
            tx_id,
            exc_info=True,
        )

    # =====================================================
    # STEP 6 — Special donor email (ASYNC)
    # =====================================================
    if email != "unknown":
        reply = SPECIAL_DONORS.get(email)
        if reply:
            try:
                create_task(send_email_reply_async(email, reply))
                log.debug(
                    "[DONATION] special email queued tx_id=%s email=%s",
                    tx_id,
                    email,
                )
            except Exception:
                log.warning(
                    "[DONATION] special email failed tx_id=%s email=%s",
                    tx_id,
                    email,
                    exc_info=True,
                )

    # =====================================================
    # STEP 7 — Normalize donation message
    # =====================================================
    donation_message, note_empty = normalize_donation_message(message)

    # =====================================================
    # STEP 8 — Parse transaction time (WIB)
    # =====================================================
    try:
        created_at = data.get("created_at")
        if created_at:
            tx_time = datetime.fromisoformat(created_at).astimezone(
                ZoneInfo("Asia/Jakarta")
            )
        else:
            tx_time = datetime.now(ZoneInfo("Asia/Jakarta"))
    except Exception:
        tx_time = datetime.now(ZoneInfo("Asia/Jakarta"))

    # =====================================================
    # STEP 9 — Send group notification (CORE OUTPUT)
    # =====================================================
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
