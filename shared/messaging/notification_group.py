import asyncio
import html

from datetime import datetime
from zoneinfo import ZoneInfo

from pyrogram.enums import ParseMode

from shared.messaging.log_proces import log_activation_failure, log_activation_success
from shared.messaging.notif.vip_messages import build_vip_message
from shared.messaging.notif.vip_utils import calculate_new_vip_end, get_basic_days
from configs.logging_setup import log

# 🕒 Durasi hapus otomatis = 10 jam (36000 detik)
AUTO_DELETE_SECONDS = 36000

# 🕑 Timezone utama = Asia/Jakarta
TZ_JAKARTA = ZoneInfo("Asia/Jakarta")


async def send_vip_group_announcement(
    app,
    chat_id,
    username: str | None,
    paket: str,
    user_id: int | None = None,
    via_voucher: bool = False,
    bonus_days: int = 0,
    tx_time: datetime | None = None,
    admin_id: int | None = None,
    mode: str | None = None,
    expired_at: datetime | None = None,
    old_vip_end: datetime | None = None,
    purchases: int = 1,
) -> dict | None:
    try:
        # ======================================================
        # 1️⃣ WAKTU TRANSAKSI (WIB)
        # ======================================================
        tx_time = tx_time or datetime.now(TZ_JAKARTA)
        if tx_time.tzinfo is None:
            tx_time = tx_time.replace(tzinfo=TZ_JAKARTA)

        # ======================================================
        # 2️⃣ NORMALISASI VIP LAMA (WIB)
        # ======================================================
        if old_vip_end:
            if old_vip_end.tzinfo is None:
                old_vip_end = old_vip_end.replace(tzinfo=TZ_JAKARTA)
            else:
                old_vip_end = old_vip_end.astimezone(TZ_JAKARTA)

            # ⛔ VIP lama expired → dianggap tidak ada
            if old_vip_end <= tx_time:
                old_vip_end = None

        # ======================================================
        # 3️⃣ DURASI PAKET
        # ======================================================
        basic_days = get_basic_days(paket)

        # ======================================================
        # 4️⃣ EXPIRED & MODE (SINGLE SOURCE)
        # ======================================================
        if mode and expired_at:
            new_vip_end = expired_at
        else:
            new_vip_end, mode = calculate_new_vip_end(
                old_vip_end=old_vip_end,
                basic_days=basic_days,
                bonus_days=bonus_days,
                via_voucher=via_voucher,
                tx_time=tx_time,
            )

        # ======================================================
        # 5️⃣ GUARD RAIL (ANTI SALAH MODE)
        # ======================================================
        if mode == "extend" and not old_vip_end:
            mode = "baru"

        if new_vip_end and new_vip_end.tzinfo is None:
            new_vip_end = new_vip_end.replace(tzinfo=TZ_JAKARTA)

        # ======================================================
        # 6️⃣ MENTION USER
        # ======================================================
        username_safe = html.escape(username or "Pengguna VIP")
        mention = (
            f"<a href='tg://user?id={user_id}'>{username_safe}</a>"
            if user_id
            else username_safe
        )

        # ======================================================
        # 7️⃣ BUILD MESSAGE
        # ======================================================
        msg_text = build_vip_message(
            username=username_safe,
            paket=paket,
            mention=mention,
            mode=mode,
            via_voucher=via_voucher,
            basic_days=basic_days,
            bonus_days=bonus_days,
            old_vip_end=old_vip_end,
            new_vip_end=new_vip_end,
            purchases=purchases,
        )

        # ======================================================
        # 8️⃣ SEND MESSAGE
        # ======================================================
        msg = await app.send_message(
            chat_id=chat_id,
            text=msg_text,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
        )

        asyncio.create_task(_auto_delete_message(msg, AUTO_DELETE_SECONDS))

        # ======================================================
        # 9️⃣ LOG SUCCESS
        # ======================================================
        return log_activation_success(
            admin_id=admin_id,
            vip_user_id=user_id,
            result={
                "paket": paket,
                "mode": mode,
                "basic_days": basic_days,
                "bonus_days": bonus_days,
                "expired_at": new_vip_end,
                "expired_lama": old_vip_end,
                "start_at": tx_time,
                "source_bot": "announce",
            },
            username=username,
        )

    except Exception as err:
        return log_activation_failure(
            admin_id=admin_id,
            vip_user_id=user_id,
            paket=paket,
            reason=str(err),
            username=username,
        )


# 🧹 Helper: Auto-delete message async
async def _auto_delete_message(msg, delay: int):
    """Hapus pesan otomatis setelah delay (detik)."""
    try:
        await asyncio.sleep(delay)
        await msg.delete()
        log.info(
            f"[VIP_ANNOUNCE][AUTO_DELETE] Pesan dihapus otomatis setelah {delay}s."
        )
    except Exception as e:
        log.warning(f"[VIP_ANNOUNCE][AUTO_DELETE] Gagal hapus pesan otomatis: {e}")
