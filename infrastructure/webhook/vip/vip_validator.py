def validate_promo_constraints(user_id, paket, paket_info):
    if not paket_info.get("is_promo_once"):
        return None

    from database.connection import get_db_cursor

    with get_db_cursor() as (cursor, _):
        cursor.execute("""
            SELECT 1 FROM vip_users
            WHERE user_id=%s AND paket=%s
              AND status='active' AND end_date>now()
            LIMIT 1
        """, (user_id, paket))

        if cursor.fetchone():
            return f"Promo {paket} hanya bisa dibeli sekali per user"

    return None
