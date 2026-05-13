from datetime import datetime, timezone

from configs.logging_setup import log
from db.connect import get_db_cursor
from db.vip_users.vip_activation import safe_insert_vip_user


def check_new_vip_entries(source_bot="drac1n"):
    try:
        with get_db_cursor() as (cursor, conn):
            cursor.execute(
                """
                SELECT id, target_user_id, paket, admin_user_id, keterangan
                FROM vip_logs
                WHERE is_notified = FALSE AND source_bot = %s
            """,
                (source_bot,),
            )
            rows = cursor.fetchall()

            for row in rows:
                log_id, user_id, paket, admin_id, keterangan = row

                # Aktivasi ulang hanya jika paket valid
                result = safe_insert_vip_user(
                    user_id=user_id,
                    paket=paket,
                    admin_id=admin_id or 999999999,  # fallback ID jika null
                    keterangan=f"[Auto-check] {keterangan or 'Tanpa keterangan'}",
                    source_bot=source_bot,
                )

                if result.get("success"):
                    cursor.execute(
                        "UPDATE vip_logs SET is_notified = TRUE WHERE id = %s",
                        (log_id,),
                    )

            conn.commit()
            print("✅ Semua entri baru berhasil diproses.")
    except Exception as e:
        log.error(f"[CHECK_VIP] ❌ Gagal memproses entri baru: {e}", exc_info=True)
