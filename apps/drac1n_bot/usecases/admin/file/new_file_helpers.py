import re

from pyrogram import Client

from configs.logging_setup import log
from database.connection import get_db_cursor

from ....utils.media_handler import get_bot_username

# =========================
# Cache
# =========================
_bot_username_cache: str | None = None

# title -> show_id (aktif sampai END)
ACTIVE_SHOWS: dict[str, int] = {}


# =========================
# 🔧 NORMALIZER
# =========================

def normalize_end_token(file_name: str) -> str:
    """
    Normalisasi variasi end / End / eNd → END
    HANYA jika nempel ke angka episode
    """
    return re.sub(
        r'(\d+(?:-\d+)?)(end)(\.\w+)$',
        r'\1END\3',
        file_name,
        flags=re.IGNORECASE,
    )


# =========================
# 🧠 PARSER
# =========================

def extract_main_title(file_name: str) -> str:
    """
    Ambil judul utama tanpa episode / END / ekstensi
    """
    file_name = normalize_end_token(file_name)

    return re.sub(
        r"""
        \s+            # spasi sebelum episode
        \d+            # episode awal
        (?:-\d+)?      # range opsional
        (?:END)?       # END opsional (SUDAH DINORMALISASI)
        \.\w+$         # ekstensi
        """,
        "",
        file_name,
        flags=re.IGNORECASE | re.VERBOSE,
    ).strip()


def is_end_file(file_name: str) -> bool:
    """
    True jika file adalah END (harus nempel ke angka)
    """
    file_name = normalize_end_token(file_name)

    return bool(
        re.search(
            r'\d+(?:-\d+)?END\.\w+$',
            file_name,
            flags=re.IGNORECASE,
        )
    )


# =========================
# 🤖 BOT UTILS
# =========================

def resolve_channel_username(chat) -> str:
    return "dracinshort"


async def get_cached_bot_username(client: Client) -> str:
    global _bot_username_cache
    if not _bot_username_cache:
        _bot_username_cache = await get_bot_username(client)
    return _bot_username_cache


# =========================
# SHOW RESOLVER (END-BASED)
# =========================
def get_show_id_from_filename(file_name: str) -> int:
    title = extract_main_title(file_name)
    is_end = is_end_file(file_name)

    with get_db_cursor(commit=True) as (cursor, conn):
        # 1️⃣ Cari show aktif terakhir
        cursor.execute(
            """
            SELECT id, series_no
            FROM shows
            WHERE title = %s AND is_completed = FALSE
            ORDER BY series_no DESC
            LIMIT 1
            """,
            (title,),
        )
        row = cursor.fetchone()

        # 2️⃣ Kalau tidak ada → buat series baru
        if not row:
            cursor.execute(
                """
                SELECT COALESCE(MAX(series_no), 0)
                FROM shows
                WHERE title = %s
                """,
                (title,),
            )
            next_series = (cursor.fetchone()[0] or 0) + 1

            cursor.execute(
                """
                INSERT INTO shows (title, series_no, genre)
                VALUES (%s, %s, %s)
                RETURNING id
                """,
                (title, next_series, "🇨🇳 Drama China")
            )
            show_id = cursor.fetchone()[0]
        else:
            show_id = row[0]

        # 3️⃣ Kalau END → tandai show selesai
        if is_end:
            cursor.execute(
                """
                UPDATE shows
                SET is_completed = TRUE
                WHERE id = %s
                """,
                (show_id,),
            )

        return show_id


def resolve_show_id_safe(file_name: str) -> int | None:
    """
    Resolve show_id dari filename.
    Return None kalau:
    - tidak ditemukan
    - ambigu
    """
    try:
        return get_show_id_from_filename(file_name)
    except Exception as e:
        log.warning(
            "[file] show_id resolve failed "
            f"filename='{file_name}' err={e}"
        )
        return None
