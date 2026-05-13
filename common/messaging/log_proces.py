from datetime import datetime
from typing import Optional

from configs.logging_setup import log

# ───────────── 🔧 Helper Functions ─────────────




def log_activation_success(
    admin_id: int,
    vip_user_id: int,
    result: dict,
    first_name: Optional[str] = None,
    username: Optional[str] = None,
) -> dict:
    """
    Log resmi aktivasi VIP (1x saja).
    Prioritas identitas: @username → first_name → user_id
    """
    user_display = (
        f"@{username}" if username
        else first_name if first_name
        else f"user_id={vip_user_id}"
    )

    paket = result.get("paket", "?")
    basic_days = result.get("basic_days", 0)
    bonus_days = result.get("bonus_days", 0)
    vip_start = result.get("start_at")
    expired_lama = result.get("expired_lama")
    expired_baru = result.get("expired_at")
    is_extend = result.get("is_extend", False)
    is_promo_once = result.get("is_promo_once", False)
    mode = "promo_once" if is_promo_once else "extend" if is_extend else "baru"
    total_hari = basic_days + bonus_days

    log.info(
        "[VIP_CONFIRM] user=%s | mode=%s | paket=%s | durasi=%s+%s hari | "
        "start=%s | expired_lama=%s | expired_baru=%s | admin=%s",
        user_display,
        mode,
        paket,
        basic_days,
        bonus_days,
        vip_start,
        expired_lama,
        expired_baru,
        admin_id,
    )

    return {
        "user_id": vip_user_id,
        "user_display": user_display,
        "paket": paket,
        "mode": mode,
        "basic_days": basic_days,
        "bonus_days": bonus_days,
        "total_hari": total_hari,
        "vip_start": vip_start,
        "expired_lama": expired_lama,
        "expired_baru": expired_baru,
        "source_bot": result.get("source_bot"),
        "is_promo_once": is_promo_once,
    }


def log_activation_failure(
    admin_id: int,
    vip_user_id: int,
    paket: str,
    reason: str,
    username: Optional[str] = None,
) -> dict:
    """
    Log kegagalan aktivasi VIP secara konsisten.
    """
    user_display = f"@{username}" if username else f"user_id={vip_user_id}"

    log.error(
        "[VIP_FAIL] ❌ Aktivasi gagal untuk %s | paket=%s | alasan=%s | oleh_admin=%s",
        user_display,
        paket,
        reason,
        admin_id,
    )

    log.info(
        "[VIP_ALERT] 🚨 User=%s, paket=%s, reason=%s, handled_by=%s",
        user_display,
        paket,
        reason,
        admin_id,
    )

    return {
        "user_id": vip_user_id,
        "username": username,
        "paket": paket,
        "reason": reason,
        "admin_id": admin_id,
    }



def log_action_start(user_id: int, vip_user_id: int | None, paket: str | None, action: str):
    log.info(
        "[VIP_FLOW] START user=%s vip_user=%s paket=%s action=%s",
        user_id,
        vip_user_id,
        paket or "-",
        action,
    )


def is_valid_data(vip_user_id: int | None, paket: str | None) -> bool:
    return bool(vip_user_id and paket)


def log_data_incomplete(user_id: int, paket: str | None = None):
    log.warning(
        "[VIP_FLOW] DATA_INCOMPLETE user=%s paket=%s",
        user_id,
        paket or "-",
    )


def log_invalid_action(user_id: int, action: str):
    log.warning(
        "[VIP_FLOW] INVALID_ACTION user=%s action=%s",
        user_id,
        action,
    )


def log_activation_cancelled(user_id: int, paket: str | None = None):
    log.info(
        "[VIP_FLOW] CANCELLED user=%s paket=%s",
        user_id,
        paket or "-",
    )
