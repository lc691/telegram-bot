# cron/vip_cleanup/vip_actions.py

from configs.logging_setup import log
from db.vip_users.vip_utils import deactivate_expired_vips


def deactivate_expired(source_bot: str | None = None) -> int:
    """
    STEP 1:
    Menonaktifkan VIP yang sudah expired.
    - Menggunakan end_date <= now() (real-time, presisi detik)
    - Sinkronisasi ke tabel users ditangani otomatis oleh trigger database
    """
    log.info("[VIP][CLEANUP] Deactivating expired VIPs...")
    return deactivate_expired_vips(
        table="vip_users",
        source_bot=source_bot,
    )
