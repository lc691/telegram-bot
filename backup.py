import base64
import datetime
import logging
import os
import subprocess
import sys
import time

from zoneinfo import ZoneInfo

import psycopg2
import schedule

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from config import PGDATABASE, PGHOST, PGPASSWORD, PGPORT, PGUSER

# ========== LOGGING ==========
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# ========== ENV SETUP UNTUK Railway ==========
SERVICE_ACCOUNT_FILE = "service_account.json"

if "GDRIVE_SERVICE_ACCOUNT_JSON" in os.environ:
    try:
        raw = os.environ["GDRIVE_SERVICE_ACCOUNT_JSON"]

        try:
            decoded = base64.b64decode(raw).decode()
            json_str = decoded
        except Exception:
            json_str = raw

        with open(SERVICE_ACCOUNT_FILE, "w") as f:
            f.write(json_str)
        logging.info("✅ Service account JSON ditulis.")
    except Exception as e:
        logging.error(f"❌ Gagal menulis service account JSON: {e}")

# ========== KONFIGURASI ==========
BACKUP_FOLDER = "./backups"
RETENTION_DAYS = 7
SCOPES = ["https://www.googleapis.com/auth/drive.file"]

# opsional: folder Google Drive
GDRIVE_FOLDER_ID = os.environ.get("GDRIVE_FOLDER_ID", None)

# Nama service DB di Railway
RAILWAY_DB_SERVICE = "postgres-db"


# ========== WAKE DB DENGAN Railway CLI ==========
def wake_db():
    try:
        logging.info("🚀 Membangunkan database via Railway CLI...")
        process = subprocess.Popen(
            ["railway", "connect", "postgres", "--service", RAILWAY_DB_SERVICE],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        time.sleep(10)
        logging.info("✅ Database sudah dibangunkan.")
        return process
    except Exception as e:
        logging.error(f"❌ Gagal membangunkan DB: {e}")
        return None


# ========== CEK DB SIAP ==========
def wait_for_db(max_retries=5, delay=5):
    for i in range(max_retries):
        try:
            logging.info(f"🔄 Coba konek DB (attempt {i+1}/{max_retries})...")
            conn = psycopg2.connect(
                dbname=PGDATABASE,
                user=PGUSER,
                password=PGPASSWORD,
                host=PGHOST,
                port=PGPORT,
                connect_timeout=5,
            )
            conn.close()
            logging.info("✅ DB online.")
            return True
        except Exception as e:
            logging.warning(f"⚠️ DB belum siap: {e}")
            time.sleep(delay)
    return False


# ========== UPLOAD KE GOOGLE DRIVE ==========
def upload_to_drive(file_path):
    try:
        credentials = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES
        )
        service = build("drive", "v3", credentials=credentials)

        file_metadata = {"name": os.path.basename(file_path)}
        if GDRIVE_FOLDER_ID:
            file_metadata["parents"] = [GDRIVE_FOLDER_ID]

        media = MediaFileUpload(file_path, resumable=True)
        result = (
            service.files()
            .create(body=file_metadata, media_body=media, fields="id")
            .execute()
        )

        logging.info(
            f"☁️ Upload ke Google Drive berhasil: {file_path} (id={result['id']})"
        )
    except Exception as e:
        logging.error(f"❌ Gagal upload ke Drive: {e}")


# ========== BACKUP POSTGRES ==========
def backup_db():
    now_wib = datetime.datetime.now(ZoneInfo("Asia/Jakarta"))
    logging.info(f"📦 Memulai backup DB (WIB: {now_wib.strftime('%Y-%m-%d %H:%M:%S')})")

    if not os.path.exists(BACKUP_FOLDER):
        os.makedirs(BACKUP_FOLDER)

    timestamp = now_wib.strftime("%Y%m%d_%H%M%S")
    backup_file = os.path.join(BACKUP_FOLDER, f"db_backup_{timestamp}.dump")

    env = os.environ.copy()
    env["PGPASSWORD"] = PGPASSWORD

    if not wait_for_db():
        logging.error("❌ DB tidak bisa dihubungi. Backup dibatalkan.")
        return

    cmd = [
        "pg_dump",
        "-h",
        PGHOST,
        "-p",
        str(PGPORT),
        "-U",
        PGUSER,
        "-d",
        PGDATABASE,
        "-F",
        "c",
        "-f",
        backup_file,
    ]

    try:
        subprocess.run(cmd, env=env, check=True)
        logging.info(f"✅ Backup berhasil: {backup_file}")
        upload_to_drive(backup_file)
        clean_old_backups()
        logging.info("🎉 Backup selesai.")
    except subprocess.CalledProcessError as e:
        logging.error(f"❌ Backup gagal: {e}")


# ========== PENGHAPUSAN BACKUP LAMA ==========
def clean_old_backups():
    now = time.time()
    for filename in os.listdir(BACKUP_FOLDER):
        file_path = os.path.join(BACKUP_FOLDER, filename)
        if os.path.isfile(file_path):
            file_age_days = (now - os.path.getmtime(file_path)) / 86400
            if file_age_days > RETENTION_DAYS:
                try:
                    os.remove(file_path)
                    logging.info(f"🗑️ Hapus backup lama: {filename}")
                except Exception as e:
                    logging.warning(f"⚠️ Gagal hapus {filename}: {e}")


# ========== JADWAL ==========
def schedule_backups():
    logging.info("📅 Jadwal backup diset ke jam 00:00 WIB setiap hari.")
    schedule.every().day.at("00:00").do(backup_db)


# ========== MAIN ==========
if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "manual":
        backup_db()

    elif len(sys.argv) > 1 and sys.argv[1] == "railway":
        logging.info("🚆 Railway mode aktif: langsung backup dan keluar")
        process = wake_db()
        backup_db()
        if process:
            process.terminate()

    else:
        logging.info("📅 Scheduler aktif. Backup otomatis setiap jam 00:00 WIB.")
        schedule_backups()
        while True:
            # logging setiap jam untuk memastikan scheduler jalan
            now_wib = datetime.datetime.now(ZoneInfo("Asia/Jakarta"))
            if now_wib.minute == 0 and now_wib.second < 2:
                logging.info(
                    f"⏰ Jam sekarang WIB: {now_wib.strftime('%Y-%m-%d %H:%M:%S')}"
                )
            schedule.run_pending()
            time.sleep(1)
