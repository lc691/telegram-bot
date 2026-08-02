from datetime import datetime, timezone

from db.connect import get_db_cursor


def get_user_info(user_id: int) -> dict:

    with get_db_cursor() as (cursor, _):

        cursor.execute(
            """
            SELECT
                paket,
                start_date,
                end_date,
                status,
                source_bot
            FROM vip_users
            WHERE user_id = %s
            LIMIT 1
            """,
            (user_id,),
        )

        row = cursor.fetchone()

    if not row:
        return {
            "is_vip": False,
            "vip_start": None,
            "vip_expired": None,
            "paket": None,
            "source_bot": None,
        }

    paket, start_date, end_date, status, source_bot = row

    now = datetime.now(timezone.utc)

    is_vip = (
        status == "active"
        and end_date
        and end_date > now
    )

    return {
        "is_vip": is_vip,
        "vip_start": start_date,
        "vip_expired": end_date,
        "paket": paket,
        "source_bot": source_bot,
        "now": now,
    }