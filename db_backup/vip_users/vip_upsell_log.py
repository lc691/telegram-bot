from db.connect import get_db_cursor


def log_upsell_event(user_id, source, target, event):
    with get_db_cursor() as (cur, _):
        cur.execute(
            """
            INSERT INTO vip_upsell_logs
            (user_id, source_paket, target_paket, event)
            VALUES (%s, %s, %s, %s)
            """,
            (user_id, source, target, event),
        )
