import os

from io import BytesIO

import numpy as np
import psycopg2
import requests

from PIL import Image
from sentence_transformers import SentenceTransformer

from config import PGDATABASE, PGHOST, PGPASSWORD, PGPORT, PGUSER

# 🔹 Load model sekali aja
print("⏳ Loading model...")
model = SentenceTransformer("clip-ViT-B-32")
print("✅ Model siap dipakai.")

# 🔹 Konfigurasi DB
USE_SSL = os.getenv("USE_RAILWAY", "0") == "1"
sslmode = "require" if USE_SSL else "disable"


def get_connection():
    return psycopg2.connect(
        host=PGHOST,
        port=PGPORT,
        dbname=PGDATABASE,
        user=PGUSER,
        password=PGPASSWORD,
        sslmode=sslmode,
    )


# 🔹 Fungsi ambil gambar dengan retry & user-agent
def fetch_image(url, retries=2, timeout=5):
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }
    for attempt in range(retries):
        try:
            resp = requests.get(url, headers=headers, timeout=timeout)
            resp.raise_for_status()
            return Image.open(BytesIO(resp.content)).convert("RGB")
        except Exception as e:
            print(f"⚠️ Gagal ambil {url} (attempt {attempt+1}/{retries}): {e}")
    return None


def main():
    conn = get_connection()
    cursor = conn.cursor()

    # 🔹 Ambil data shows
    cursor.execute(
        "SELECT id, thumbnail_url FROM shows WHERE thumbnail_url IS NOT NULL;"
    )
    shows = cursor.fetchall()
    print(f"🔍 Ditemukan {len(shows)} show dengan thumbnail_url.")

    counter = 0
    for show_id, thumbnail_url in shows:
        # 🔹 Skip kalau sudah ada embedding
        cursor.execute("SELECT 1 FROM show_embeddings WHERE show_id = %s", (show_id,))
        if cursor.fetchone():
            print(f"⏭️ Embedding show_id={show_id} sudah ada, skip.")
            continue

        # 🔹 Ambil gambar
        img = fetch_image(thumbnail_url)
        if img is None:
            print(f"❌ Gagal proses show_id={show_id}, skip.")
            continue

        try:
            embedding = model.encode(img)
            embedding_list = (
                embedding.tolist() if isinstance(embedding, np.ndarray) else embedding
            )

            cursor.execute(
                """
                INSERT INTO show_embeddings (show_id, vector)
                VALUES (%s, %s)
                ON CONFLICT (show_id) DO UPDATE SET vector = excluded.vector
                """,
                (show_id, embedding_list),
            )

            counter += 1
            if counter % 50 == 0:
                conn.commit()
                print(f"💾 Commit batch ke-{counter // 50}")

            print(f"✅ Berhasil simpan embedding show_id={show_id}")

        except Exception as e:
            conn.rollback()
            print(f"❌ Error embedding show_id={show_id}: {e}")

    # 🔹 Commit sisa batch terakhir
    conn.commit()
    cursor.close()
    conn.close()
    print("🎉 Selesai.")


if __name__ == "__main__":
    main()
