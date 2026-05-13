import base64
import json
import os
import time

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from cron.config import GDRIVE_FOLDER_ID, SCOPES, SERVICE_ACCOUNT_FILE
from cron.logger import setup_logger

log = setup_logger("gdrive")

def prepare_service_account():
    raw = os.environ.get("GDRIVE_SERVICE_ACCOUNT_JSON")
    if not raw:
        log.info("Service account env tidak ada, upload dinonaktifkan")
        return False

    try:
        data = raw if raw.strip().startswith("{") else base64.b64decode(raw).decode()
        json.loads(data)
        with open(SERVICE_ACCOUNT_FILE, "w") as f:
            f.write(data)
        log.info("Service account siap")
        return True
    except Exception:
        log.exception("Gagal menyiapkan service account")
        return False


def upload(file_path, retries=3):
    if not os.path.exists(SERVICE_ACCOUNT_FILE):
        return

    for attempt in range(1, retries + 1):
        try:
            creds = service_account.Credentials.from_service_account_file(
                SERVICE_ACCOUNT_FILE, scopes=SCOPES
            )
            service = build("drive", "v3", credentials=creds)

            metadata = {"name": os.path.basename(file_path)}
            if GDRIVE_FOLDER_ID:
                metadata["parents"] = [GDRIVE_FOLDER_ID]

            media = MediaFileUpload(file_path, resumable=True)
            service.files().create(
                body=metadata, media_body=media, fields="id"
            ).execute()

            log.info("☁️ Upload ke Drive berhasil: %s", file_path)
            return
        except Exception:
            log.exception("Upload gagal, retry %d", attempt)
            time.sleep(2 ** attempt)
