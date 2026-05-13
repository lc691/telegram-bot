from configs.logging_setup import log

from .vip_queries import deactivate_expired_vips_db, set_vip_notified
from .vip_time import calculate_vip_range


# ===============================
# 🔹 Deactivate VIP Expired
# ===============================
def deactivate_expired_vips(source_bot: str | None = None) -> int:
    """
    Menonaktifkan VIP yang sudah expired.
    Sinkronisasi ke tabel users ditangani oleh trigger database.
    """
    count = deactivate_expired_vips_db(source_bot)
    log.info(
        "[VIP AUTO OFF] ✅ %s VIP expired dinonaktifkan%s",
        count,
        f" (bot={source_bot})" if source_bot else "",
    )
    return count


# ===============================
# 🔹 Parsing Range VIP (UI only)
# ===============================
def parse_vip_dates(expired_at, total_days: int):
    """
    Utility UI untuk menampilkan range VIP.
    Tidak mempengaruhi logic VIP.
    """
    start_dt, expired_dt = calculate_vip_range(expired_at, total_days)
    if not start_dt:
        return "—", "—"

    return (
        start_dt.strftime("%d %b %Y %H:%M"),
        expired_dt.strftime("%d %b %Y %H:%M"),
    )


# ===============================
# 🔹 Reminder Flag (users.vip_reminded)
# ===============================
def mark_vip_notified(user_id: int):
    """
    Tandai bahwa user sudah dikirimi reminder VIP.
    """
    set_vip_notified(user_id, True)
    log.info("[VIP NOTIFIED] ✅ vip_reminded=TRUE user_id=%s", user_id)


def reset_vip_notified(user_id: int):
    """
    Reset reminder VIP (dipanggil otomatis oleh trigger).
    """
    set_vip_notified(user_id, False)
    log.info("[VIP NOTIFIED] 🔁 vip_reminded=FALSE user_id=%s", user_id)
