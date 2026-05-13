from cron.logger import setup_logger

log = setup_logger("cleanup")

try:
    from run_vip_cleanup import run_vip_cleanup
except Exception:
    def run_vip_cleanup():
        log.warning("run_vip_cleanup() tidak ditemukan, skip")

def execute_cleanup():
    log.info("🧹 Menjalankan VIP Cleanup...")
    run_vip_cleanup()
