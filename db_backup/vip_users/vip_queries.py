from datetime import datetime, timezone

from db.connect import get_dict_cursor


def get_random_non_vip_users(limit: int = 5) -> list[dict]:
    """
    Ambil user acak dari tabel users yang tidak punya VIP aktif.
    """
    with get_dict_cursor() as (cursor, _):
        cursor.execute(
            """
            SELECT user_id, username, first_name
            FROM users
            WHERE
                (is_vip = FALSE OR vip_expired < now())
                AND user_id IS NOT NULL
            ORDER BY RANDOM()
            LIMIT %s
            """,
            (limit,),
        )
        return cursor.fetchall()


def is_user_vip(user_id: int) -> bool:
    """
    Cek apakah user punya status VIP aktif di tabel vip_users.
    """
    with get_dict_cursor() as (cursor, _):
        cursor.execute(
            """
            SELECT 1
            FROM vip_users
            WHERE user_id = %s AND status = 'active' AND end_date > now()
            LIMIT 1
            """,
            (user_id,),
        )
        return cursor.fetchone() is not None
