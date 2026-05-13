import html

from datetime import datetime
from zoneinfo import ZoneInfo

from common.messaging.vip_message_builder import generate_vip_message_to_user
from configs.logging_setup import log


def build_success_message(
    user,
    admin_user,
    vip_user_id: int,
    result: dict,
    source_bot: str,
    vip_start: datetime = None,
    vip_end: datetime = None,
) -> str:
    """
    Membuat pesan sukses aktivasi VIP untuk user.
    """

    # =====================================================
    # Step 1: Normalize timezone (ke WIB)
    # =====================================================
    if vip_start and vip_start.tzinfo:
        vip_start = vip_start.astimezone(ZoneInfo("Asia/Jakarta"))
    if vip_end and vip_end.tzinfo:
        vip_end = vip_end.astimezone(ZoneInfo("Asia/Jakarta"))

    # =====================================================
    # Step 2: Ambil info user (escape HTML biar aman)
    # =====================================================
    first_name = html.escape(getattr(user, "first_name", None) or "Anonim")
    username = html.escape(user.username) if getattr(user, "username", None) else None

    # =====================================================
    # Step 3: Tentukan mode (baru / extend / promo_once)
    # =====================================================
    if result.get("is_promo_once"):
        mode = "promo_once"
    elif result.get("is_extend"):
        mode = "extend"
    else:
        mode = "baru"

    # =====================================================
    # Step 4: Bangun pesan utama untuk user
    # =====================================================
    user_msg = generate_vip_message_to_user(
        first_name=first_name,
        username=username,
        user_id=vip_user_id,
        paket=result.get("paket", "-"),
        vip_start=vip_start,
        vip_end=vip_end,
        is_extend=result.get("is_extend", False),
        is_promo_once=result.get("is_promo_once", False),
        purchases=result.get("purchases", 0),
        bonus=result.get("bonus_days", 0),
    )

    # =====================================================
    # Step 5: Tambahkan info admin yang mengaktifkan
    # =====================================================
    if admin_user:
        if getattr(admin_user, "username", None):
            admin_name = f"@{html.escape(admin_user.username)}"
        else:
            admin_name = html.escape(getattr(admin_user, "first_name", "Sistem"))
    else:
        admin_name = "Sistem"

    # =====================================================
    # Step 6: Escape bot source (fallback UnknownBot)
    # =====================================================
    source_bot_safe = html.escape(source_bot or "UnknownBot")

    # =====================================================
    # Step 7: Gabungkan semua jadi pesan final
    # =====================================================
    msg = (
        f"{user_msg}\n\n"
        f"🔧 <b>Diaktifkan oleh:</b> {admin_name}\n"
        f"🤖 <b>Bot Sumber:</b> <code>{source_bot_safe}</code>"
    )

    # =====================================================
    # Step 8: Logging
    # =====================================================
    log.info(
        f"[VIP_USER_MSG] Pesan sukses siap dikirim "
        f"user_id={vip_user_id} paket={result.get('paket')} "
        f"mode={mode} bonus={result.get('bonus_days', 0)}"
    )

    return msg
