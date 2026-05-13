# cron/vip_cleanup/vip_stats.py

from db.connect import get_dict_cursor


def count_active_vips() -> int:
    """
    Hitung jumlah VIP yang masih aktif.
    VIP aktif jika status = 'active' dan end_date > now().
    """
    with get_dict_cursor() as (cursor, _):
        cursor.execute(
            """
            SELECT COUNT(*) AS total
            FROM vip_users
            WHERE status = 'active'
              AND (end_date IS NULL OR end_date > now())
            """
        )
        row = cursor.fetchone()
        return row["total"] if row else 0
