import os

from cron.logger import setup_logger
from cron.scheduler import daily_job

log = setup_logger("main")


def detect_source() -> str:
    """
    Menentukan sumber eksekusi:
    - railway-cron : dijalankan oleh Railway Cron
    - manual       : dijalankan manual / local
    """
    return "railway-cron" if os.environ.get("RAILWAY_ENVIRONMENT") else "manual"


if __name__ == "__main__":
    source = detect_source()

    log.info("[CRON] Triggered by %s", source)

    daily_job(source=source)

    log.info("[CRON] Exit")

