import time
import sys
from typing import Optional, List, Tuple

from configs.logging_setup import setup_logger, log
from db.connect import get_dict_cursor

from bots.caridrama_bot.infrastructure.embedding.clip_model import encode_image
from bots.caridrama_bot.infrastructure.image.image_fetcher import fetch_image


SLEEP_EVERY = 10
SLEEP_SEC = 1.0


# ======================================================
# FETCH TARGET LIST (DB SAFE)
# ======================================================
def fetch_targets(force: bool, limit: Optional[int]) -> List[Tuple[int, str]]:
    with get_dict_cursor() as (cur, _):
        query = """
            SELECT show_id, thumbnail_url
            FROM show_embeddings
            WHERE thumbnail_url IS NOT NULL
              AND (%s OR vector IS NULL)
            ORDER BY show_id
        """
        params = [force]

        if limit is not None:
            query += " LIMIT %s"
            params.append(limit)

        cur.execute(query, tuple(params))
        rows = cur.fetchall()

    return [(r["show_id"], r["thumbnail_url"]) for r in rows]


# ======================================================
# SAVE SINGLE EMBEDDING (RECONNECT SAFE)
# ======================================================
def save_embedding(show_id: int, url: str, vector: list[float]) -> None:
    with get_dict_cursor(commit=True) as (cur, _):
        cur.execute(
            """
            INSERT INTO show_embeddings (show_id, vector, thumbnail_url)
            VALUES (%s, %s, %s)
            ON CONFLICT (show_id) DO UPDATE
            SET vector = EXCLUDED.vector,
                thumbnail_url = EXCLUDED.thumbnail_url
            """,
            (show_id, vector, url),
        )


# ======================================================
# MAIN MIGRATION
# ======================================================
def migrate_embeddings(
    *,
    limit: Optional[int] = None,
    force: bool = False,
):
    start = time.time()

    targets = fetch_targets(force, limit)
    total = len(targets)

    log.info("[MIGRATE] 🎯 Target embeddings: %d", total)

    if not targets:
        log.info("[MIGRATE] Tidak ada data untuk diproses.")
        return

    updated = 0

    for i, (show_id, url) in enumerate(targets, start=1):
        try:
            img = fetch_image(url)
            if not img:
                log.warning("[MIGRATE] ⚠️ Skip show_id=%s (image fetch failed)", show_id)
                continue

            vec = encode_image(img).tolist()

            save_embedding(show_id, url, vec)
            updated += 1

            if updated % 5 == 0:
                log.info("[MIGRATE] 💾 Progress: %d/%d", updated, total)

            if i % SLEEP_EVERY == 0:
                time.sleep(SLEEP_SEC)

        except KeyboardInterrupt:
            log.warning("[MIGRATE] 🛑 Dihentikan manual")
            break
        except Exception:
            log.exception("[MIGRATE] ❌ Gagal show_id=%s", show_id)

    log.info(
        "[MIGRATE] ✅ Selesai | updated=%d/%d | %.2fs",
        updated,
        total,
        time.time() - start,
    )


# ======================================================
# ENTRY POINT
# ======================================================
if __name__ == "__main__":
    setup_logger()

    force = "--force" in sys.argv
    limit = None

    for arg in sys.argv:
        if arg.startswith("--limit="):
            limit = int(arg.split("=", 1)[1])

    migrate_embeddings(
        limit=limit,
        force=force,
    )
