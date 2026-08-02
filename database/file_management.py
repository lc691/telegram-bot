from typing import Optional, Tuple
from uuid import uuid4

from configs.logging_setup import log
from database.connection import get_db_cursor

# =========================== #
# === FILE MANAGEMENT     === #
# =========================== #


def save_file_metadata(
    *,
    file_id: str,
    file_name: str,
    channel_username: str,
    file_type: str,
    file_size: int,
    show_id: Optional[int],
    is_paid: bool,
) -> Optional[Tuple[str, str]]:
    """
    Simpan metadata file (FREE / PAID).

    Return:
        (free_hash, paid_hash) jika berhasil
        None jika file sudah ada / gagal
    """

    try:
        with get_db_cursor(commit=True) as (cursor, _):
            # ==================================================
            # 1️⃣ DUPLICATE CHECK (METADATA-LEVEL)
            # ==================================================
            cursor.execute(
                """
                SELECT free_hash, paid_hash
                FROM files
                WHERE file_name = %s
                  AND file_size = %s
                  AND file_type = %s
                """,
                (file_name, file_size, file_type),
            )
            row = cursor.fetchone()
            if row:
                log.info(
                    "[FILE] duplicate skipped name='%s' size=%s type=%s",
                    file_name,
                    file_size,
                    file_type,
                )
                return row["free_hash"], row["paid_hash"]

            # ==================================================
            # 2️⃣ GENERATE HASH
            # ==================================================
            base_hash = str(uuid4())
            free_hash = base_hash
            paid_hash = f"vip_{base_hash}"

            # ==================================================
            # 3️⃣ INSERT FILE METADATA
            # ==================================================
            cursor.execute(
                """
                INSERT INTO files (
                    file_id,
                    file_name,
                    free_hash,
                    paid_hash,
                    channel_username,
                    file_type,
                    file_size,
                    show_id,
                    is_paid
                )
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """,
                (
                    file_id,
                    file_name,
                    free_hash,
                    paid_hash,
                    channel_username,
                    file_type,
                    file_size,
                    show_id,
                    is_paid,
                ),
            )

            # ==================================================
            # 4️⃣ UPLOAD LOG (BEST EFFORT)
            # ==================================================
            cursor.execute(
                """
                INSERT INTO file_upload_log (file_id, uploader)
                VALUES (%s, %s)
                ON CONFLICT DO NOTHING
                """,
                (file_id, channel_username),
            )

            log.info(
                "[FILE] saved name='%s' show_id=%s is_paid=%s",
                file_name,
                show_id,
                is_paid,
            )

            return free_hash, paid_hash

    except Exception:
        log.exception("[FILE] save_file_metadata failed name='%s'", file_name)
        return None


def check_or_save_file(
    cursor,
    conn,
    file_id: str,
    file_name: str,
    channel_username: str,
    file_type: str,
    file_size: int,
    is_paid: bool,
    show_id: Optional[int] = None,
):
    try:
        cursor.execute(
            """
            SELECT free_hash, paid_hash
            FROM files
            WHERE file_name = %s AND file_size = %s AND file_type = %s
            """,
            (file_name, file_size, file_type),
        )
        if cursor.fetchone():
            log.info("File '%s' sudah ada (duplikat metadata).", file_name)
            return None, None

        unique_hash = str(uuid4())
        free_hash = unique_hash
        paid_hash = f"vip_{unique_hash}"

        cursor.execute(
            """
            INSERT INTO files (
                file_id, file_name,
                free_hash, paid_hash,
                channel_username,
                file_type, file_size,
                show_id, is_paid
            )
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                file_id,
                file_name,
                free_hash,
                paid_hash,
                channel_username,
                file_type,
                file_size,
                show_id,
                is_paid,
            ),
        )

        cursor.execute(
            """
            INSERT INTO file_upload_log (file_id, uploader)
            VALUES (%s, %s)
            ON CONFLICT DO NOTHING
            """,
            (file_id, channel_username),
        )

        return free_hash, paid_hash

    except Exception:
        conn.rollback()
        raise



def get_latest_upload_logs(cursor, limit: int = 10):
    """
    Ambil daftar log upload terbaru, default maksimal 10.
    """
    cursor.execute(
        """
        SELECT file_id, uploader, uploaded_at
        FROM file_upload_log
        ORDER BY uploaded_at DESC
        LIMIT %s
        """,
        (limit,),
    )
    return cursor.fetchall()


def delete_old_upload_logs(cursor, conn, days: int = 30):
    """
    Hapus log upload yang lebih lama dari `days` hari.
    """
    try:
        cursor.execute(
            """
            DELETE FROM file_upload_log
            WHERE uploaded_at < NOW() - INTERVAL '%s days'
            """,
            (days,),
        )
        conn.commit()
        log.info("Log upload lebih dari %s hari dihapus.", days)
    except Exception as e:
        log.error("Gagal menghapus log lama: %s", e, exc_info=True)


def get_or_create_show_id(cursor, conn, title: str) -> int:
    cursor.execute("SELECT id FROM shows WHERE title ILIKE %s", (title,))
    row = cursor.fetchone()

    if row:
        show_id = row[0]
        log.info(f"[SHOW] Ditemukan ID {show_id} untuk judul '{title}'")
        return show_id

    # Otomatis set genre saat tambah show baru
    genre = "🇨🇳 Drama China"
    cursor.execute(
        "INSERT INTO shows (title, genre) VALUES (%s, %s) RETURNING id",
        (title, genre),
    )
    new_id = cursor.fetchone()[0]
    conn.commit()

    log.warning(
        f"[SHOW] Judul baru '{title}' berhasil DITAMBAHKAN ke tabel shows dengan ID={new_id} dan genre='{genre}'"
    )
    return new_id
