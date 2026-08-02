from datetime import datetime, timedelta, timezone

from pyrogram.types import Message

from shared.utils.parse_date import ensure_aware
from configs.logging_setup import log


from .repository import get_user, update_vip_reminder

VIP_WARNING_THRESHOLD = timedelta(days=1)


async def remind_vip_if_needed(user_id: int, now: datetime, message: Message):
    """
    Kirim reminder jika VIP user akan habis dalam 1 hari.
    - user_id: int
    - now: datetime aware
    - message: pyrogram Message object untuk reply
    """
    user = get_user(user_id)
    if not user:
        # log.info(f"[Reminder] User {user_id} belum ada → skip reminder")
        return

    # Ambil VIP aktif
    vip_expired = user.get("vip_expired")
    if not vip_expired:
        return

    vip_expired = ensure_aware(vip_expired)
    delta = vip_expired - now

    if delta <= timedelta(0) or delta > VIP_WARNING_THRESHOLD:
        # VIP masih aman / sudah expired → skip
        return

    if user.get("vip_reminded"):
        log.debug(f"[Reminder] User {user_id} sudah diingatkan → skip")
        return

    # --- Kirim reminder ---
    try:
        await message.reply_text(
            "⚠️ VIP kamu akan habis besok.\nPerpanjang sekarang via /vip!"
        )
        # log.info(f"[Reminder] Reminder VIP dikirim ke user_id={user_id}")

        # Tandai sudah diingatkan
        update_vip_reminder(user_id, reminded=True)

    except Exception as e:
        log.warning(
            f"[Reminder] Gagal kirim reminder user_id={user_id}: {e}", exc_info=True
        )
