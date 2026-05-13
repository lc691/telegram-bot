import asyncio
import time
import ipaddress

from configs.logging_setup import log
from db.connect import get_dict_cursor

# =====================================================
# CACHE GLOBAL
# =====================================================
_trusted_ips_cache: set[str] = set()
_last_load_time: float = 0.0
CACHE_TTL = 300  # detik
_lock = asyncio.Lock()

DEFAULT_TRUSTED_IPS = {
    "100.64.0.9",
    "103.123.45.68",
}


def is_valid_ip_or_cidr(value: str) -> bool:
    try:
        if "/" in value:
            ipaddress.ip_network(value, strict=False)
        else:
            ipaddress.ip_address(value)
        return True
    except ValueError:
        return False


async def _load_from_db() -> set[str]:
    """
    Dipisah supaya bisa future: async DB / threadpool
    """
    with get_dict_cursor() as (cursor, _):
        cursor.execute("SELECT ip FROM trusted_ips")
        rows = cursor.fetchall()
        return {r["ip"] for r in rows}


async def load_trusted_ips() -> set[str]:
    global _trusted_ips_cache, _last_load_time

    now = time.monotonic()

    # =================================================
    # FAST PATH (CACHE HIT)
    # =================================================
    if now - _last_load_time < CACHE_TTL and _trusted_ips_cache:
        return _trusted_ips_cache

    async with _lock:
        now = time.monotonic()

        # double check
        if now - _last_load_time < CACHE_TTL and _trusted_ips_cache:
            return _trusted_ips_cache

        try:
            raw_ips = await _load_from_db()

            # =================================================
            # VALIDASI DATA
            # =================================================
            valid_ips = {ip for ip in raw_ips if is_valid_ip_or_cidr(ip)}

            invalid_count = len(raw_ips) - len(valid_ips)

            if invalid_count:
                log.warning(
                    "[WEBHOOK] invalid trusted IP skipped count=%s",
                    invalid_count,
                )

            if not valid_ips:
                raise ValueError("No valid trusted IPs from DB")

            _trusted_ips_cache = valid_ips
            _last_load_time = now

            log.info(
                "[WEBHOOK] Trusted IPs refreshed count=%s",
                len(_trusted_ips_cache),
            )

        except Exception as e:
            log.error("[WEBHOOK] Failed load trusted IPs: %s", e)

            # =================================================
            # FALLBACK STRATEGY
            # =================================================
            if _trusted_ips_cache:
                log.warning(
                    "[WEBHOOK] Using STALE cache count=%s",
                    len(_trusted_ips_cache),
                )
            else:
                _trusted_ips_cache = DEFAULT_TRUSTED_IPS.copy()
                log.warning(
                    "[WEBHOOK] Using DEFAULT trusted IPs count=%s",
                    len(_trusted_ips_cache),
                )

    return _trusted_ips_cache
