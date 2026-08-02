# db/stats/donation_aggregates.py
from database.connection import get_db_cursor


def get_vip_donation_per_day(days=7, bot_name="drac1n"):
    with get_db_cursor() as (cursor, _):
        cursor.execute(
            """
            SELECT DATE(timestamp) AS tanggal, SUM(amount) AS total
            FROM donation_log
            WHERE timestamp >= CURRENT_DATE - INTERVAL %s
              AND type = 'vip'
              AND source_bot = %s
            GROUP BY tanggal
            ORDER BY tanggal
            """,
            (f"{days} days", bot_name),
        )
        return cursor.fetchall()  # list of tuples: (tanggal, total)
