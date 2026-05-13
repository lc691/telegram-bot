from configs.logging_setup import log
from db.connect import get_autocommit_cursor, get_db_cursor, get_dict_cursor


def get_all_request_sources(offset: int = 0, limit: int = 5) -> list[tuple[str, str]]:
    """
    Ambil source dari DB dengan pagination.
    Return: list of (code, label)
    """
    with get_dict_cursor() as (cursor, _):
        cursor.execute(
            "SELECT code, label FROM request_sources ORDER BY id ASC OFFSET %s LIMIT %s",
            (offset, limit),
        )
        rows = cursor.fetchall()
        return [(row["code"], row["label"]) for row in rows]


def count_all_request_sources() -> int:
    """
    Hitung total source di DB.
    """
    with get_dict_cursor() as (cursor, _):
        cursor.execute("SELECT COUNT(*) FROM request_sources")
        total = cursor.fetchone()[0]
        return total


def get_sources(offset=0, limit=5):
    """
    Ambil list source dari database dengan pagination.
    """
    query = """
        SELECT id, code, label
        FROM request_sources
        ORDER BY id ASC
        OFFSET %s
        LIMIT %s
    """
    with get_dict_cursor() as (cursor, _):
        cursor.execute(query, (offset, limit))
        rows = cursor.fetchall()
        return rows


def count_sources():
    """
    Hitung total source yang ada di database.
    """
    query = "SELECT COUNT(*) FROM request_sources"
    with get_dict_cursor() as (cursor, _):
        cursor.execute(query)
        total = cursor.fetchone()[0]
        return total


def add_request_source(code: str, label: str) -> bool:
    try:
        with get_autocommit_cursor() as cursor:
            cursor.execute(
                "INSERT INTO request_sources (code, label) VALUES (%s, %s)",
                (code, label),
            )
        return True
    except Exception as e:
        log.warning(f"⚠️ Gagal menambah source '{code}': {e}")
        return False


def delete_source_by_id(source_id: int):
    query = "DELETE FROM request_sources WHERE id = %s"
    with get_db_cursor(commit=True) as (cursor, _):
        cursor.execute(query, (source_id,))


def request_source_exists(code: str) -> bool:
    with get_dict_cursor() as (cursor, _):
        cursor.execute("SELECT 1 FROM request_sources WHERE code = %s", (code,))
        return cursor.fetchone() is not None


def is_valid_source(code: str) -> bool:
    try:
        with get_dict_cursor() as (cursor, _):
            cursor.execute("SELECT 1 FROM request_sources WHERE code = %s", (code,))
            return cursor.fetchone() is not None
    except Exception as e:
        log.warning(f"[DB] Gagal validasi source '{code}': {e}")
        return False


def search_sources_by_keyword(keyword: str) -> list[tuple[str, str]]:
    query = """
        SELECT code, label
        FROM request_sources
        WHERE label ILIKE %s
        ORDER BY label ASC
        LIMIT 10
    """
    with get_dict_cursor() as (cursor, _):
        cursor.execute(query, (f"%{keyword}%",))
        rows = cursor.fetchall()
        return [(row["code"], row["label"]) for row in rows]
