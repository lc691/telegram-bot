from configs.logging_setup import log
from database.connection import get_dict_cursor


def get_package_by_name(paket_name: str) -> dict | None:
    """
    Ambil detail 1 paket VIP dari tabel vip_packages.
    """
    try:
        with get_dict_cursor() as (cursor, conn):
            cursor.execute(
                """
                SELECT *
                FROM vip_packages
                WHERE paket_name = %s
                  AND is_active = true
                """,
                (paket_name,),
            )
            row = cursor.fetchone()
            return dict(row) if row else None
    except Exception as e:
        log.exception(f"[DB] Gagal ambil paket {paket_name}: {e}")
        return None


def get_active_packages() -> list[dict]:
    """
    Ambil semua paket VIP yang aktif.
    """
    try:
        with get_dict_cursor() as (cursor, conn):
            cursor.execute(
                """
                SELECT *
                FROM vip_packages
                WHERE is_active = true
                ORDER BY total_days ASC
                """
            )
            rows = cursor.fetchall()
            return [dict(r) for r in rows] if rows else []
    except Exception as e:
        log.exception(f"[DB] Gagal ambil daftar paket aktif: {e}")
        return []
