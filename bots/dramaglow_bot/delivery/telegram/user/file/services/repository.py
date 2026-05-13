# services/files/repository.py
import re

from configs.logging_setup import log
from db.connect import get_dict_cursor


def get_file(file_db_id: int):
    with get_dict_cursor() as (cur, _):
        cur.execute(
            """
            SELECT
                f.id,
                f.show_id,
                f.file_name,
                f.file_id,
                f.file_type,
                f.is_paid,
                f.channel_username,
                COALESCE(f.message_id, sf.message_id) AS message_id
            FROM files f
            LEFT JOIN show_files sf ON sf.file_id = f.id
            WHERE f.id = %s
            """,
            (file_db_id,),
        )
        return cur.fetchone()


def can_access_file(is_vip: bool, free_remaining: int) -> bool:
    """Cek apakah user boleh akses file berikutnya."""
    return is_vip or free_remaining > 0


def extract_part_number(file_name: str) -> int:
    """
    Untuk file range episode:
    judul 1-20.mp4
    judul 21-40.mp4
    judul 41-60END.mp4

    Ambil angka PERTAMA sebagai penentu urutan range.
    """
    name = file_name.upper()

    # Ambil ANGKA PERTAMA SAJA, tanpa peduli END
    m = re.search(r"(\d+)", name)
    if m:
        return int(m.group(1))

    log.warning("[NAV] invalid filename (no number): %s", file_name)
    return 999999
