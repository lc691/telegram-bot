from typing import Any, Dict, Optional, Union

from configs.logging_setup import log
from db.connect import get_db_cursor, get_dict_cursor
from db.vip_users.vip_activation import safe_insert_vip_user


def get_active_vip_count() -> int:
    with get_db_cursor() as (cur, _):
        cur.execute(
            """
            SELECT COUNT(*) FROM vip_users
            WHERE status = 'active'
              AND end_date > NOW()
        """
        )
        return cur.fetchone()[0]


KEY_LAST_VIP = "last_vip_given"


def get_active_vip(user_id: int, source_bot: str = "drac1n") -> dict | None:
    """
    Mengambil VIP aktif terbaru dari tabel vip_users untuk user tertentu.
    Return: dict berisi kolom `end_date` (dan lainnya jika diperlukan), atau None jika tidak ada.
    """
    try:
        with get_dict_cursor() as (cursor, _):
            cursor.execute(
                """
                SELECT user_id, end_date, start_date, paket
                FROM vip_users
                WHERE user_id = %s AND source_bot = %s AND status = 'active'
                ORDER BY end_date DESC
                LIMIT 1
                """,
                (user_id, source_bot),
            )
            return cursor.fetchone()
    except Exception as e:

        log.error(
            f"[get_active_vip] Gagal ambil data VIP untuk user_id={user_id}: {e}",
            exc_info=True,
        )
        return None


def give_vip(
    user_id: int,
    username: str,
    durasi_hari: int,
    paket: str,
    keterangan: str = "",
    source: str = "manual",
    by_admin_id: Optional[int] = None,
    source_bot: str = "drac1n",
    target_bot: str = "drac1n",
    batch_uuid: Optional[str] = None,
) -> Dict[str, Union[bool, Any]]:
    try:
        result = safe_insert_vip_user(
            user_id=user_id,
            username=username or "-",
            paket=paket,
            durasi_hari=durasi_hari,
            admin_id=by_admin_id or 0,
            keterangan=keterangan,
            source=source,
            source_bot=source_bot,
            target_bot=target_bot,
            batch_uuid=batch_uuid,  # ✅ Teruskan
        )
        return {"success": True, "data": result}
    except Exception as e:

        log.error(
            f"[give_vip] ❌ Gagal assign VIP: user_id={user_id}, username={username}, durasi={durasi_hari} hari, error={e}",
            exc_info=True,
        )
        return {"success": False, "error": str(e)}
