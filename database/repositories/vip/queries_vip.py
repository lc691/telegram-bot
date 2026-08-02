from configs.logging_setup import log


def upsert_vip_user(cur, user_id, username, start, end, paket, source_bot):
    cur.execute("""
        INSERT INTO vip_users (
            user_id, username, start_date, end_date,
            paket, status, source_bot, updated_at
        )
        VALUES (%s, %s, %s, %s, %s, 'active', %s, NOW())
        ON CONFLICT (user_id, source_bot)
        DO UPDATE SET
            username = EXCLUDED.username,
            start_date = EXCLUDED.start_date,
            end_date = EXCLUDED.end_date,
            paket = EXCLUDED.paket,
            status = 'active',
            updated_at = NOW()
    """, (user_id, username, start, end, paket, source_bot))

    log.info(f"[VIP] 💾 vip_users upsert sukses user_id={user_id}")


def insert_vip_log(cur, data):
    cur.execute("""
        INSERT INTO vip_logs (
            target_user_id, admin_user_id, paket,
            basic_days, bonus_days, durasi_hari,
            is_extend, expired_baru, keterangan,
            source, source_bot, target_bot, batch_uuid, promo_once
        )
        VALUES (%(user_id)s, %(admin_id)s, %(paket)s,
                %(basic_days)s, %(bonus_days)s, %(durasi)s,
                %(is_extend)s, %(expired)s, %(ket)s,
                %(source)s, %(source_bot)s, %(target_bot)s,
                %(batch)s, %(promo)s)
        ON CONFLICT ON CONSTRAINT uniq_vip_logs_batch_uuid
        DO NOTHING
        RETURNING id
    """, data)

    return cur.fetchone()


def count_user_purchases(cur, user_id):
    cur.execute("SELECT COUNT(*) FROM vip_logs WHERE target_user_id = %s", (user_id,))
    return cur.fetchone()["count"]
