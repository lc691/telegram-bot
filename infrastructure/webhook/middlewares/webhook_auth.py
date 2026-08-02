import secrets
import ipaddress
from fastapi import Request
from fastapi.responses import JSONResponse

from config import MANUAL_TRX_TOKEN, TRAKTEER_SECRET_KEY
from configs.logging_setup import log
from infrastructure.webhook.services.client_ip import get_real_client_ip
from infrastructure.webhook.services.trusted_ip import load_trusted_ips


def ip_in_whitelist(ip: str, whitelist: list[str]) -> bool:
    try:
        ip_obj = ipaddress.ip_address(ip)
        for w in whitelist:
            if "/" in w:
                if ip_obj in ipaddress.ip_network(w):
                    return True
            else:
                if ip == w:
                    return True
    except Exception:
        return False
    return False


async def webhook_auth(request: Request):
    client_ip = get_real_client_ip(request)
    token = request.headers.get("x-webhook-token")
    cf_worker = request.headers.get("cf-worker")

    trusted_ips = await load_trusted_ips()

    # =================================================
    # MANUAL / ADMIN
    # =================================================
    if token == MANUAL_TRX_TOKEN:
        if not ip_in_whitelist(client_ip, trusted_ips):
            log.warning("[AUTH] manual rejected ip=%s", client_ip)
            return JSONResponse({"error": "Unauthorized"}, status_code=401)

        log.info("[AUTH] manual granted ip=%s", client_ip)
        return None

    # =================================================
    # TRAKTEER OFFICIAL
    # =================================================
    if secrets.compare_digest(token or "", TRAKTEER_SECRET_KEY):

        # ❗ OPTIONAL: IP check jangan wajib
        if trusted_ips and not ip_in_whitelist(client_ip, trusted_ips):
            log.warning("[AUTH] trakteer ip not in whitelist ip=%s", client_ip)

        # Validasi tambahan header
        if cf_worker != "trakteer.id":
            log.warning("[AUTH] invalid cf-worker ip=%s value=%s", client_ip, cf_worker)
            return JSONResponse({"error": "Unauthorized"}, status_code=401)

        log.info("[AUTH] trakteer verified ip=%s", client_ip)
        return None

    # =================================================
    # INVALID
    # =================================================
    log.warning("[AUTH] invalid token ip=%s", client_ip)
    return JSONResponse({"error": "Unauthorized"}, status_code=401)
