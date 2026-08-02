import datetime

from shared.utils.admin_notifier import notify_admin_error
from scheduler.cleanup import execute_cleanup
from scheduler.config import TIMEZONE
from scheduler.db import backup_db
from scheduler.lock import acquire_lock, release_lock, write_last_run
from scheduler.logger import setup_logger

log = setup_logger("cron")


def guard_only_midnight():
    now = datetime.datetime.now(TIMEZONE)
    if now.hour != 0:
        log.warning(
            "[GUARD] Skip execution (not midnight) | WIB=%s",
            now.strftime("%Y-%m-%d %H:%M:%S"),
        )
        return False
    return True


def daily_job(source="unknown"):
    if not guard_only_midnight():
        log.warning("[CRON] Abort | source=%s", source)
        return

    if not acquire_lock():
        log.warning("Job masih berjalan, skip")
        return

    try:
        log.info("[CRON][START] source=%s", source)

        # === VIP CLEANUP ===
        try:
            execute_cleanup()
        except Exception as e:
            log.exception("[CRON][ERROR] VIP Cleanup gagal")
            notify_admin_error(
                title="❌ CRON: VIP Cleanup Gagal",
                message=str(e),
                source=source,
            )
            return  # STOP cron (opsional, tapi disarankan)

        # === DB BACKUP ===
        try:
            backup_db()
        except Exception as e:
            log.exception("[CRON][ERROR] Backup DB gagal")
            notify_admin_error(
                title="❌ CRON: Backup DB Gagal",
                message=str(e),
                source=source,
            )
            return

        write_last_run(datetime.datetime.now(TIMEZONE).date().isoformat())
        log.info("[CRON][FINISH] Job selesai")

    finally:
        release_lock()
