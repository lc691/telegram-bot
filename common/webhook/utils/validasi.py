import re

from typing import Optional

from configs.logging_setup import log
from db.vip_users.vip_db_utils import get_vip_package_info


def validate_and_extract_vip_info(
    message: str,
    amount: int,
    *,
    supporter_name: str | None = None,
    log_analysis: bool = False,  # default OFF
) -> tuple[Optional[int], Optional[str], str]:
    """
    Validasi pesan supporter dan ekstrak informasi VIP.
    """

    if log_analysis:
        log.debug(
            "[VALIDATOR] Incoming message=%r amount=%s supporter=%s",
            message,
            amount,
            supporter_name,
        )

    # ❌ Supporter private
    if supporter_name and supporter_name.lower() == "seseorang":
        log.info("[VALIDATOR] Private supporter → ignored")
        return None, None, "unknown"

    try:
        match = re.fullmatch(
            r"(daftar_short|daftar_utbk)_(\d+)_(\w+)",
            (message or "").strip(),
            re.IGNORECASE,
        )
        if not match:
            log.warning("[VALIDATOR] Invalid message format")
            return None, None, "unknown"

        prefix, user_id_str, paket_alias = match.groups()
        paket_alias = paket_alias.lower()
        prefix = prefix.lower()

        # Validasi user_id
        try:
            user_id = int(user_id_str)
            if user_id <= 0:
                raise ValueError
        except ValueError:
            log.warning("[VALIDATOR] Invalid user_id=%r", user_id_str)
            return None, None, "unknown"

        source_bot = "utbk" if prefix == "daftar_utbk" else "drac1n"

        paket_info = get_vip_package_info(paket_alias)
        if log_analysis:
            log.debug("[VALIDATOR] Paket lookup alias=%s found=%s", paket_alias, bool(paket_info))

        if not paket_info:
            log.warning(
                "[VALIDATOR] Paket not found alias=%s user_id=%s",
                paket_alias,
                user_id,
            )
            return user_id, None, source_bot

        expected_price = paket_info.get("price", 0)
        if amount < expected_price:
            log.warning(
                "[VALIDATOR] Price mismatch user_id=%s paket=%s paid=%s expected=%s",
                user_id,
                paket_alias,
                amount,
                expected_price,
            )
            return user_id, None, source_bot

        paket_final = paket_info["paket"]
        log.info(
            "[VALIDATOR] VIP validated user_id=%s paket=%s bot=%s",
            user_id,
            paket_final,
            source_bot,
        )

        return user_id, paket_final, source_bot

    except Exception:
        log.exception("[VALIDATOR] Failed to parse supporter message")
        return None, None, "unknown"
