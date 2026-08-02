from datetime import datetime, timezone

from db.connect import get_db_cursor
from db.vip_users.vip_activation import safe_insert_vip_user
from db.vip_users.vip_db_utils import (
    get_vip_package_info,
)


def check_new_donation_entries(source_bot="drac"):
    try:
        with get_db_cursor() as (cursor, conn):
            cursor.execute(
                """
                SELECT id, user_id, paket, amount, message
                FROM donation_log
                WHERE status = 'success' AND is_notified = FALSE AND source_bot = %s
            """,
                (source_bot,),
            )
            rows = cursor.fetchall()

            for row in rows:
                log_id, user_id, paket, amount, message = row

                # Pastikan paket valid
                if not get_vip_package_info(paket):
                    continue

                # Gunakan activate_vip
                result = safe_insert_vip_user(
                    user_id=user_id,
                    paket=paket,
                    admin_id=999999999,  # default/fallback untuk otomatis
                    keterangan=f"[AUTO] Donasi: {message or '-'}",
                    source_bot=source_bot,
                )

                if result.get("success"):
                    cursor.execute(
                        """
                        UPDATE donation_log
                        SET is_notified = TRUE,
                            confirmed_at = NOW()
                        WHERE id = %s
                    """,
                        (log_id,),
                    )

            conn.commit()
            print("✅ Semua donasi sukses diproses jadi VIP.")
    except Exception as e:
        from configs.logging_setup import log


        log.error(f"[DONATION_CHECK] ❌ Gagal proses donasi: {e}", exc_info=True)
