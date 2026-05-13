from configs.logging_setup import log
from db.connect import get_db_cursor


def get_dashboard_stats():
    """Mengambil statistik untuk dashboard admin dari berbagai tabel database."""
    stats = {
        "total_users": 0,
        "users_drac1n": 0,
        "users_utbk": 0,
        "vip_drac1n": 0,
        "vip_utbk": 0,
        "total_vip": 0,
        "vip_percentage": 0,
        "total_plays": 0,
        "total_files": 0,
        "total_amount": 0,
        "total_donasi": 0,
        "total_vip_donation": 0,
        "total_admins": 0,
        "new_users_today": 0,
    }

    queries = {
        "users_drac1n": "SELECT COUNT(*) FROM users",
        "users_utbk": "SELECT COUNT(*) FROM users_utbk",
        "vip_drac1n": "SELECT COUNT(*) FROM users WHERE is_vip = TRUE",
        "vip_utbk": "SELECT COUNT(*) FROM users_utbk WHERE is_vip = TRUE",
        "total_plays": "SELECT COALESCE(SUM(play_count), 0) FROM video_stats",
        "total_files": "SELECT COUNT(*) FROM files",
        "total_amount": "SELECT COALESCE(SUM(amount), 0) FROM donation_log",
        "total_donasi": "SELECT COALESCE(SUM(amount), 0) FROM donation_log WHERE type = 'donasi'",
        "total_vip_donation": "SELECT COALESCE(SUM(amount), 0) FROM donation_log WHERE type = 'vip'",
        "total_admins": "SELECT COUNT(*) FROM admins",
        "new_users_today": "SELECT COUNT(*) FROM users WHERE DATE(created_at) = CURRENT_DATE",
    }

    try:
        with get_db_cursor() as (cursor, _):
            for key, query in queries.items():
                try:
                    cursor.execute(query)
                    result = cursor.fetchone()
                    stats[key] = result[0] if result and result[0] is not None else 0
                except Exception as q_err:
                    log.warning(f"[Dashboard Stats] Gagal query '{key}': {q_err}")
                    stats[key] = 0

            stats["total_users"] = stats["users_drac1n"] + stats["users_utbk"]
            stats["total_vip"] = stats["vip_drac1n"] + stats["vip_utbk"]
            if stats["total_users"]:
                stats["vip_percentage"] = round(
                    stats["total_vip"] / stats["total_users"] * 100, 1
                )
            else:
                stats["vip_percentage"] = 0

        log.info("[Dashboard Stats] Statistik berhasil diperoleh.")
        return stats

    except Exception as e:
        log.error(
            f"[Dashboard Stats] ❌ Gagal mengambil data keseluruhan: {e}", exc_info=True
        )
        return None
