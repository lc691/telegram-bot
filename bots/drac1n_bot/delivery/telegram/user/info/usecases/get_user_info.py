from datetime import datetime, timezone

from db.connect import get_db_cursor


def get_user_info(user_id: int) -> dict:
    with get_db_cursor() as (cursor, _):
        cursor.execute(
            """
            SELECT is_vip, vip_start, vip_expired
            FROM users
            WHERE user_id = %s
            """,
            (user_id,),
        )
        row = cursor.fetchone()

    if not row:
        return {
            "is_vip": False,
            "vip_start": None,
            "vip_expired": None,
        }

    is_vip, vip_start, vip_expired = row

    return {
        "is_vip": is_vip,
        "vip_start": vip_start,
        "vip_expired": vip_expired,
        "now": datetime.now(timezone.utc),
    }
