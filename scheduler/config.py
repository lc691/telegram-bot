import os

from zoneinfo import ZoneInfo

# === GENERAL ===
BACKUP_FOLDER = os.environ.get("BACKUP_FOLDER", "./backups")
RETENTION_DAYS = int(os.environ.get("RETENTION_DAYS", "7"))
TIMEZONE = ZoneInfo("Asia/Jakarta")

LOCK_FILE = os.path.join(BACKUP_FOLDER, ".running")
LAST_RUN_FILE = os.path.join(BACKUP_FOLDER, ".last_run_date")

# === DATABASE ===
PGDATABASE = os.environ.get("PGDATABASE")
PGHOST = os.environ.get("PGHOST")
PGPASSWORD = os.environ.get("PGPASSWORD")
PGPORT = int(os.environ.get("PGPORT", "5432"))
PGUSER = os.environ.get("PGUSER")

# === GOOGLE DRIVE ===
SERVICE_ACCOUNT_FILE = os.environ.get(
    "SERVICE_ACCOUNT_FILE", "service_account.json"
)
GDRIVE_FOLDER_ID = os.environ.get("GDRIVE_FOLDER_ID")
SCOPES = ["https://www.googleapis.com/auth/drive.file"]
