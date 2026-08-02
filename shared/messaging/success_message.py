import html

from datetime import datetime
from zoneinfo import ZoneInfo

from shared.messaging.vip_message_builder import (
    generate_vip_message_to_user,
)
from configs.logging_setup import log


WIB = ZoneInfo("Asia/Jakarta")


def _to_wib(dt: datetime | None) -> datetime | None:
    """
    Convert datetime ke WIB.
    """

    if not dt:
        return None

    # naive datetime diasumsikan UTC
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=ZoneInfo("UTC"))

    return dt.astimezone(WIB)


def build_success_message(
    user,
    admin_user,
    vip_user_id: int,
    result: dict,
    source_bot: str,
    vip_start: datetime | None = None,
    vip_end: datetime | None = None,
) -> str:
    """
    Build pesan sukses aktivasi VIP untuk user.
    """

    # =====================================================
    # STEP 1 — Normalize datetime ke WIB
    # =====================================================

    vip_start = _to_wib(vip_start)
    vip_end = _to_wib(vip_end)

    # =====================================================
    # STEP 2 — Safe user info
    # =====================================================

    first_name = html.escape(
        getattr(user, "first_name", None) or "Anonim"
    )

    username = getattr(user, "username", None)

    username = (
        html.escape(username)
        if username
        else None
    )

    # =====================================================
    # STEP 3 — Mode info
    # =====================================================

    is_extend = result.get("is_extend", False)
    is_promo_once = result.get("is_promo_once", False)

    if is_promo_once:
        mode = "promo_once"
    elif is_extend:
        mode = "extend"
    else:
        mode = "baru"

    # =====================================================
    # STEP 4 — Generate user message
    # =====================================================

    user_msg = generate_vip_message_to_user(
        first_name=first_name,
        username=username,
        user_id=vip_user_id,
        paket=result.get("paket", "-"),
        vip_start=vip_start,
        vip_end=vip_end,
        is_extend=is_extend,
        is_promo_once=is_promo_once,
        purchases=max(1, result.get("purchases", 1)),
        bonus=result.get("bonus_days", 0),
    )

    # =====================================================
    # STEP 5 — Admin info
    # =====================================================

    if admin_user:

        admin_username = getattr(
            admin_user,
            "username",
            None,
        )

        if admin_username:
            admin_name = f"@{html.escape(admin_username)}"

        else:
            admin_name = html.escape(
                getattr(
                    admin_user,
                    "first_name",
                    "Sistem",
                )
            )

    else:
        admin_name = "Sistem"

    # =====================================================
    # STEP 6 — Source bot
    # =====================================================

    source_bot_safe = html.escape(
        source_bot or "UnknownBot"
    )

    # =====================================================
    # STEP 7 — Final message
    # =====================================================

    msg = (
        f"{user_msg}\n\n"
        f"🔧 <b>Diaktifkan oleh:</b> {admin_name}\n"
        f"🤖 <b>Bot Sumber:</b> "
        f"<code>{source_bot_safe}</code>"
    )

    # =====================================================
    # STEP 8 — Logging
    # =====================================================

    log.info(
        "[VIP_USER_MSG] "
        "user_id=%s paket=%s mode=%s "
        "start=%s end=%s bonus=%s",
        vip_user_id,
        result.get("paket"),
        mode,
        vip_start,
        vip_end,
        result.get("bonus_days", 0),
    )

    return msg
