from pyrogram.enums import ParseMode

from configs.logging_setup import log
from database.connection import get_db_cursor, get_dict_cursor

from .normalize_main_title import normalize_for_match


def get_files_from_db():
    """
    Ambil seluruh file dari database.
    Mengembalikan list tuple: (id, file_id, file_name, free_hash, paid_hash, file_type).
    """
    try:
        with get_db_cursor() as (cursor, conn):
            cursor.execute(
                "SELECT id, file_id, file_name, free_hash, paid_hash, file_type FROM files"
            )
            return cursor.fetchall()
    except Exception as e:
        log.error(f"[DB] ❌ Gagal ambil data file: {e}")
        return None


def get_files_by_hash(access_hash: str):
    """
    Ambil file dari DB berdasarkan free_hash atau paid_hash.
    Mengembalikan tuple: (id, file_id, name, free_hash, paid_hash, file_type) atau None jika tidak ditemukan.
    """
    if not access_hash:
        return None

    try:
        with get_dict_cursor() as (cursor, _):
            cursor.execute(
                """
                SELECT
                    id,
                    file_id,
                    file_name AS name,
                    free_hash,
                    paid_hash,
                    file_type
                FROM files
                WHERE free_hash = %s OR paid_hash = %s
            """,
                (access_hash, access_hash),
            )
            return cursor.fetchone()
    except Exception as e:

        log.error(
            f"[get_files_by_hash] access_hash={access_hash} Error: {e}", exc_info=True
        )
        return None


def file_with_title_exists(title: str) -> bool:
    query = """
        SELECT 1 FROM files
        WHERE file_name ILIKE %s
        LIMIT 1
    """
    with get_dict_cursor() as (cursor, _):
        cursor.execute(query, (f"%{title}%",))
        return cursor.fetchone() is not None


def update_main_title_and_message_id_auto(judul_caption, message_id):
    """
    Update main_title dan message_id secara otomatis:
    - Jika hanya 1 baris yang cocok, update 1 baris pakai ctid.
    - Jika lebih dari 1, update semua baris yang cocok.
    """
    like_pattern = f"{judul_caption.strip()}%"

    with get_db_cursor(commit=True) as (cursor, conn):
        # Cari semua baris yang cocok
        cursor.execute(
            "SELECT ctid FROM files WHERE file_name ILIKE %s", (like_pattern,)
        )
        rows = cursor.fetchall()

        if not rows:
            log.warning(f"⚠️ Tidak ditemukan file_name LIKE '{like_pattern}'")
            return

        if len(rows) == 1:
            # Update 1 baris saja pakai ctid
            ctid = rows[0][0]
            update_query = """
                UPDATE files
                SET main_title = %s,
                    message_id = %s
                WHERE ctid = %s
            """
            cursor.execute(update_query, (judul_caption.strip(), message_id, ctid))
            log.info(
                f"✅ Update 1 baris dengan main_title '{judul_caption.strip()}' berhasil"
            )
        else:
            # Update semua baris yang cocok sekaligus
            update_query = """
                UPDATE files
                SET main_title = %s,
                    message_id = %s
                WHERE file_name ILIKE %s
            """
            cursor.execute(
                update_query, (judul_caption.strip(), message_id, like_pattern)
            )
            log.info(
                f"✅ Update {cursor.rowcount} baris dengan main_title '{judul_caption.strip()}' berhasil"
            )


def bulk_insert_initial_views(view_data: dict[str, int]):
    """
    Menambahkan view awal untuk banyak file berdasarkan hash.
    view_data: {hash_value: view_count}
    Fungsi ini otomatis mendeteksi apakah hash termasuk free_hash atau paid_hash.
    """
    try:
        with get_db_cursor() as (cursor, conn):
            hashes = list(view_data.keys())

            # 1️⃣ Ambil file_id yang cocok dengan hash (free_hash atau paid_hash)
            cursor.execute(
                """
                SELECT file_id, free_hash, paid_hash
                FROM files
                WHERE free_hash = ANY(%s) OR paid_hash = ANY(%s)
                """,
                (hashes, hashes),
            )
            results = cursor.fetchall()

            if not results:
                log.warning("[DB] Tidak ada file yang cocok dengan hash yang diberikan")
                return

            # Buat mapping hash -> file_id
            hash_to_file_id = {}
            for file_id, free_hash, paid_hash in results:
                if free_hash in view_data:
                    hash_to_file_id[free_hash] = file_id
                if paid_hash in view_data:
                    hash_to_file_id[paid_hash] = file_id

            # 2️⃣ Insert ke video_stats (play_count=0, last_played=NOW())
            video_stats_tuples = [(fid, 0) for fid in hash_to_file_id.values()]
            cursor.executemany(
                """
                INSERT INTO video_stats (file_id, play_count, last_played)
                VALUES (%s, %s, NOW())
                ON CONFLICT (file_id) DO NOTHING
                """,
                video_stats_tuples,
            )

            # 3️⃣ Insert/update ke file_views
            view_tuples = [(h, v) for h, v in view_data.items()]
            cursor.executemany(
                """
                INSERT INTO file_views (hash, views)
                VALUES (%s, %s)
                ON CONFLICT (hash)
                DO UPDATE SET views = EXCLUDED.views
                """,
                view_tuples,
            )

            conn.commit()
            log.info(
                f"[DB] ✅ View awal berhasil ditambahkan untuk {len(view_tuples)} hash"
            )

    except Exception as e:
        log.error(f"❌ Gagal menambahkan view awal (bulk): {e}")


def get_post_by_main_title(title: str):
    """
    Cari row yang main_title cocok (case-insensitive), dan message_id tidak NULL.
    """
    query = """
        SELECT id, file_name, file_id, message_id, channel_username
        FROM files
        WHERE LOWER(main_title) = LOWER(%s)
        AND message_id IS NOT NULL
        LIMIT 1
    """
    with get_dict_cursor() as (cursor, conn):
        cursor.execute(query, (title,))
        row = cursor.fetchone()
        return row


def update_main_title_and_message_id_safe(judul_caption, message_id):
    """
    - Simpan judul ASLI (dengan ! , ?)
    - Matching pakai judul BERSIH
    - Tidak overwrite data lama
    - Guard dari salah judul
    """

    original_title = judul_caption.strip()  # disimpan ke DB
    like_pattern = normalize_for_match(original_title)  # dipakai untuk LIKE

    with get_db_cursor(commit=True) as (cursor, conn):
        cursor.execute(
            """
            SELECT ctid, file_name
            FROM files
            WHERE LOWER(file_name) LIKE %s
              AND (main_title IS NULL OR main_title = '')
            """,
            (like_pattern,),
        )
        rows = cursor.fetchall()

        if not rows:
            log.warning(f"⚠️ Tidak ditemukan file cocok untuk '{original_title}'")
            return

        # 🚨 Guard keamanan
        if len(rows) > 100:
            log.error(
                f"🚨 Terlalu banyak match ({len(rows)}) "
                f"untuk '{original_title}'. Update dibatalkan."
            )
            return

        # ===============================
        # UPDATE
        # ===============================
        if len(rows) == 1:
            cursor.execute(
                """
                UPDATE files
                SET main_title = %s,
                    message_id = %s
                WHERE ctid = %s
                """,
                (original_title, message_id, rows[0][0]),
            )
            log.info(f"✅ Update 1 file: {rows[0][1]}")

        else:
            cursor.execute(
                """
                UPDATE files
                SET main_title = %s,
                    message_id = %s
                WHERE LOWER(file_name) LIKE %s
                  AND (main_title IS NULL OR main_title = '')
                """,
                (original_title, message_id, like_pattern),
            )
            log.info(
                f"✅ Update {cursor.rowcount} file " f"dengan judul '{original_title}'"
            )


from configs.logging_setup import log
from database.connection import get_db_cursor


def update_show_file_message_id_safe(
    show_file_id: int,
    message_id: int,
) -> None:
    """
    Update message_id untuk show_files dengan aman
    - Tidak overwrite jika sudah sama
    - Trigger sync_files akan otomatis jalan
    """

    with get_db_cursor(commit=True) as (cursor, _):
        cursor.execute(
            """
            UPDATE show_files
            SET message_id = %s
            WHERE id = %s
              AND (message_id IS NULL OR message_id != %s)
            """,
            (message_id, show_file_id, message_id),
        )

        if cursor.rowcount:
            log.info(
                "[show_files] message_id updated "
                f"show_file_id={show_file_id} msg_id={message_id}"
            )
        else:
            log.debug(
                "[show_files] message_id unchanged "
                f"show_file_id={show_file_id} msg_id={message_id}"
            )


def increment_view_count(hash_value: str):
    try:
        with get_db_cursor(commit=True) as (cursor, _):

            # UPSERT + INCREMENT + UPDATE last_played
            cursor.execute(
                """
                INSERT INTO video_stats (file_id, play_count, last_played)
                SELECT f.file_id, 1, NOW()
                FROM files f
                WHERE f.free_hash = %s OR f.paid_hash = %s
                ON CONFLICT (file_id)
                DO UPDATE
                SET play_count = video_stats.play_count + 1,
                    last_played = NOW()
                """,
                (hash_value, hash_value),
            )

            # Optional: tetap simpan counter agregat
            cursor.execute(
                """
                INSERT INTO file_views (hash, views)
                VALUES (%s, 1)
                ON CONFLICT (hash)
                DO UPDATE SET views = file_views.views + 1
                """,
                (hash_value,),
            )

    except Exception:
        log.exception(
            "[STATS] increment_view_count failed hash=%s",
            hash_value,
        )


def get_hashes_by_main_title(main_title: str) -> list[str]:
    query = """
        SELECT free_hash, paid_hash
        FROM files
        WHERE LOWER(main_title) = LOWER(%s)
    """
    with get_dict_cursor() as (cursor, _):
        cursor.execute(query, (main_title,))
        rows = cursor.fetchall()
        hashes = []
        for row in rows:
            free_hash, paid_hash = row
            if free_hash:
                hashes.append(free_hash)
            if paid_hash:
                hashes.append(paid_hash)
        return hashes


def get_free_hashes_by_main_title(main_title: str) -> list[str]:
    query = """
        SELECT free_hash
        FROM files
        WHERE LOWER(TRIM(main_title)) = LOWER(TRIM(%s))
          AND free_hash IS NOT NULL
    """
    with get_dict_cursor() as (cursor, _):
        cursor.execute(query, (main_title,))
        rows = cursor.fetchall()
        return [row[0] for row in rows if row[0]]


def get_existing_view_hashes() -> set[str]:
    query = "SELECT hash FROM file_views"
    with get_dict_cursor() as (cursor, _):
        cursor.execute(query)
        rows = cursor.fetchall()
        return set(row["hash"] for row in rows if row["hash"])
