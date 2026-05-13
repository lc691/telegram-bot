from asyncio import create_task
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from bots.bots_registry import get_bot
from configs.logging_setup import log

from common.webhook.middlewares.webhook_auth import webhook_auth
from common.webhook.transaction.regular_handler import process_regular_donation
from common.webhook.transaction.vip_handler import process_vip_transaction
from common.webhook.utils.parsing import extract_message
from common.webhook.utils.trakteer_transactions import (
    calculate_amount,
    is_transaction_processed,
    save_transaction,
)
from common.webhook.utils.validasi import validate_and_extract_vip_info


app = FastAPI()


@app.post("/webhook/trakteer")
async def handle_trakteer(request: Request):
    # =================================================
    # 1️⃣ AUTH (middleware-style)
    # =================================================
    auth_response = await webhook_auth(request)
    if auth_response:
        return auth_response

    # =================================================
    # 2️⃣ PARSE PAYLOAD
    # =================================================
    try:
        content_type = (request.headers.get("content-type") or "").lower()

        if "application/json" in content_type:
            data = await request.json()
        elif "application/x-www-form-urlencoded" in content_type:
            data = dict(await request.form())
        else:
            log.warning("unsupported_content_type type=%s", content_type)
            return JSONResponse({"error": "Unsupported content-type"}, status_code=415)

        transaction_id = data.get("transaction_id")
        if not transaction_id:
            log.info("ignored missing transaction_id")
            return JSONResponse(
                {"status": "ignored", "reason": "missing transaction_id"},
                status_code=200,
            )

    except Exception:
        log.exception("payload_parse_failed")
        return JSONResponse({"error": "Invalid payload"}, status_code=400)

    log.info("webhook accepted trx_id=%s", transaction_id)

    # =================================================
    # 3️⃣ DUPLICATE GUARD
    # =================================================
    if is_transaction_processed(transaction_id):
        log.info("duplicate ignored trx_id=%s", transaction_id)
        return JSONResponse(
            {"status": "success", "message": "duplicate ignored"},
            status_code=200,
        )

    # =================================================
    # 4️⃣ PAYMENT PARSING
    # =================================================
    try:
        amount, source = calculate_amount(data)
        log.info(
            "payment parsed trx_id=%s amount=%s source=%s",
            transaction_id,
            amount,
            source,
        )
    except Exception:
        log.exception("payment_parse_failed trx_id=%s", transaction_id)
        return JSONResponse(
            {"status": "error", "message": "Invalid payment data"},
            status_code=400,
        )

    # =================================================
    # 5️⃣ VIP VALIDATION
    # =================================================
    message = extract_message(data) or ""
    user_id_vip, paket, source_bot = validate_and_extract_vip_info(
        message,
        amount,
        supporter_name=data.get("supporter_name"),
    )

    # =================================================
    # 6️⃣ BOT RESOLUTION
    # =================================================
    client = get_bot(source_bot) or get_bot("drac1n")
    if not client:
        log.error(
            "bot_not_available bot=%s trx_id=%s",
            source_bot,
            transaction_id,
        )
        return JSONResponse(
            {"error": f"Bot '{source_bot}' not available"},
            status_code=404,
        )

    # =================================================
    # 7️⃣ VIP PROCESSING (ASYNC, SAFE)
    # =================================================
    if user_id_vip and paket:
        try:
            save_transaction(
                transaction_id,
                data,
                user_id=user_id_vip,
                paket=paket,
                source_bot=source_bot,
                amount=amount,
            )

            async def safe_vip_task():
                try:
                    await process_vip_transaction(
                        client,
                        data,
                        message,
                        source_bot,
                        user_id_vip,
                        paket,
                        amount,
                    )
                except Exception:
                    log.exception(
                        "[VIP_TASK] failed trx_id=%s user_id=%s",
                        transaction_id,
                        user_id_vip,
                    )

            create_task(safe_vip_task())

            log.info(
                "vip queued trx_id=%s user_id=%s paket=%s bot=%s",
                transaction_id,
                user_id_vip,
                paket,
                source_bot,
            )

            return JSONResponse(
                {"status": "success", "message": "VIP queued"},
                status_code=200,
            )

        except Exception:
            log.exception("vip_processing_failed trx_id=%s", transaction_id)
            return JSONResponse(
                {"status": "error", "message": "VIP processing failed"},
                status_code=500,
            )

    # =================================================
    # 8️⃣ REGULAR DONATION
    # =================================================
    try:
        result, _ = await process_regular_donation(
            client,
            data,
            message,
            source_bot,
        )

        save_transaction(
            transaction_id,
            data,
            source_bot=source_bot,
            amount=amount,
        )

        log.info(
            "regular processed trx_id=%s bot=%s result=%s",
            transaction_id,
            source_bot,
            result,
        )

        return JSONResponse(
            {"status": "success", "message": result},
            status_code=200,
        )

    except Exception:
        log.exception("regular_processing_failed trx_id=%s", transaction_id)
        return JSONResponse(
            {"status": "error", "message": "Regular donation failed"},
            status_code=500,
        )
