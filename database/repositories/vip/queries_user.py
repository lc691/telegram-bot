from configs.logging_setup import log


def ensure_user_exists(cur, user_id, username):
    cur.execute("SELECT 1 FROM users WHERE user_id = %s", (user_id,))
    if not cur.fetchone():
        cur.execute("""
            INSERT INTO users (user_id, username, is_vip, vip_expired, created_at, updated_at)
            VALUES (%s, %s, FALSE, NULL, NOW(), NOW())
            ON CONFLICT (user_id) DO NOTHING
        """, (user_id, username))
        log.info(f"[VIP] 👤 Auto insert user baru user_id={user_id}")


def get_active_vip_row(cur, user_id, source_bot):
    cur.execute("""
        SELECT start_date, end_date
        FROM vip_users
        WHERE user_id = %s
          AND source_bot = %s
          AND status = 'active'
    """, (user_id, source_bot))
    return cur.fetchone()
