import datetime
import os
import shutil
import subprocess
import time

import psycopg2

from cron.config import *
from cron.gdrive import upload
from cron.logger import setup_logger

log = setup_logger("db")

def wait_for_db(retries=6, delay=5):
    for i in range(retries):
        try:
            psycopg2.connect(
                dbname=PGDATABASE,
                user=PGUSER,
                password=PGPASSWORD,
                host=PGHOST,
                port=PGPORT,
                connect_timeout=5,
            ).close()
            return True
        except Exception:
            log.warning("DB belum siap (%d/%d)", i + 1, retries)
            time.sleep(delay)
    return False


def clean_old_backups():
    now = time.time()
    for f in os.listdir(BACKUP_FOLDER):
        path = os.path.join(BACKUP_FOLDER, f)
        if os.path.isfile(path):
            age = (now - os.path.getmtime(path)) / 86400
            if age > RETENTION_DAYS:
                os.remove(path)
                log.info("🗑️ Hapus backup lama: %s", f)


def backup_db():
    os.makedirs(BACKUP_FOLDER, exist_ok=True)

    if shutil.which("pg_dump") is None:
        log.error("pg_dump tidak tersedia")
        return

    if not wait_for_db():
        log.error("DB tidak bisa dihubungi")
        return

    ts = datetime.datetime.now(TIMEZONE).strftime("%Y%m%d_%H%M%S")
    output = os.path.join(BACKUP_FOLDER, f"db_backup_{ts}.dump")

    env = os.environ.copy()
    env["PGPASSWORD"] = PGPASSWORD or ""

    cmd = [
        "pg_dump",
        "-h", PGHOST,
        "-p", str(PGPORT),
        "-U", PGUSER,
        "-d", PGDATABASE,
        "-F", "c",
        "-f", output,
    ]

    subprocess.run(cmd, env=env, check=True)
    log.info("📦 Backup selesai: %s", output)

    upload(output)
    clean_old_backups()
