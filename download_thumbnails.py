import os
import time

import psycopg2
import requests

from slugify import slugify

DB = {
    "dbname": "railway",
    "user": "postgres",
    "password": "noFWOLNMzIJcAwDmwcuhMhzccAWhpelx",
    "host": "ballast.proxy.rlwy.net",
    "port": 45970,
}

OUTPUT_DIR = "thumbnails"
os.makedirs(OUTPUT_DIR, exist_ok=True)

session = requests.Session()
session.headers.update(
    {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/123 Safari/537.36"}
)


def stable_download(url, retry=5):
    """
    Download dengan retry otomatis
    """
    for attempt in range(1, retry + 1):
        try:
            print(f"  ▶ Percobaan {attempt}/{retry} ...")
            r = session.get(url, timeout=40, stream=True)

            if r.status_code == 200:
                return r.content

            print(f"  ❌ Status: {r.status_code}")

        except Exception as e:
            print(f"  ❌ Error: {e}")

        # Fallback ke HTTP (Catbox sering lebih stabil)
        if url.startswith("https://"):
            url = url.replace("https://", "http://")

        time.sleep(2)

    return None


def download_all():
    conn = psycopg2.connect(**DB)
    cur = conn.cursor()

    cur.execute(
        "SELECT title, thumbnail_url FROM shows WHERE thumbnail_url IS NOT NULL"
    )
    rows = cur.fetchall()

    for title, url in rows:
        print(f"\n⬇️  Downloading: {title}")
        print(f"URL: {url}")

        data = stable_download(url)

        if not data:
            print(f"❌ Gagal total: {url}")
            continue

        folder_name = slugify(title)
        folder_path = os.path.join(OUTPUT_DIR, folder_name)
        os.makedirs(folder_path, exist_ok=True)

        file_ext = os.path.splitext(url)[1]
        if not file_ext:
            file_ext = ".jpg"

        file_path = os.path.join(folder_path, slugify(title) + file_ext)

        with open(file_path, "wb") as f:
            f.write(data)

        print(f"✅ Saved: {file_path}")


if __name__ == "__main__":
    download_all()
