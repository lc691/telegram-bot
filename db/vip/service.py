from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytz

from psycopg2 import errors

from common.bot_utils import get_table_name
from common.utils.parse_date import ensure_aware
from configs.logging_setup import log
from db.connect import get_db_cursor, get_dict_cursor
from db.vip_users.vip_db_utils import get_vip_package_info

# Zona waktu resmi Indonesia (WIB)
JAKARTA_TZ = pytz.timezone("Asia/Jakarta")


def safe_insert_vip_user(
    user_id: int,
    username: str,
    paket: str,
    durasi_hari: int = None,
    basic_days: int = 0,
    bonus_days: int = 0,
    keterangan: str = "",
    source: str = "manual",
    source_bot: str = "drac1n",
    target_bot: str = "drac1n",
    admin_id: int = 0,
    batch_uuid: str = None,
    is_promo_once: bool = False,
):
    """
    ✅ Fungsi final untuk menambah atau memperpanjang VIP user.

    PERHITUNGAN WAKTU:
    -------------------
    - Semua waktu disimpan & dihitung dalam zona waktu Asia/Jakarta (WIB)
    - Jika user beli "1 hari", maka VIP berlaku 24 jam penuh.
      Contoh:
        Start : 2025-10-30 17:00:00 WIB
        End   : 2025-10-31 17:00:00 WIB
    - Tidak dipotong ke jam 23:59:59, karena itu membuat durasi kurang dari 24 jam.

    LOGIKA DASAR:
    -------------
    1. Jika belum pernah VIP → buat entri baru
    2. Jika masih aktif → extend (tambah durasi_hari dari end_date lama)
    3. Jika sudah kadaluarsa → reset dari waktu saat ini
    """

    # === 0. Inisialisasi ===
    now_jakarta = datetime.now(JAKARTA_TZ)
    start_date = now_jakarta
    end_date = None
    expired_lama = None

    # ⚠️ JANGAN percaya default
    is_extend = False

    # === 1. Hitung total durasi ===
    if durasi_hari is None:
        durasi_hari = basic_days + bonus_days

    try:
        with get_dict_cursor() as (cur, conn):
            log.info(
                "[VIP] START user=%s paket=%s durasi=%s basic=%s bonus=%s",
                user_id, paket, durasi_hari, basic_days, bonus_days
            )

            # === 2. Pastikan user ada di tabel users ===
            cur.execute("SELECT 1 FROM users WHERE user_id = %s", (user_id,))
            if not cur.fetchone():
                cur.execute(
                    """
                    INSERT INTO users (user_id, username, is_vip, vip_expired, created_at, updated_at)
                    VALUES (%s, %s, FALSE, NULL, NOW(), NOW())
                    ON CONFLICT (user_id) DO NOTHING
                    """,
                    (user_id, username),
                )
                log.info(f"[VIP] 👤 Auto-insert user baru → user_id={user_id}")

            # === 3. Cek apakah user punya VIP aktif ===
            row = None
            if not is_promo_once:
                cur.execute(
                    """
                    SELECT start_date, end_date
                    FROM vip_users
                    WHERE user_id = %s
                      AND source_bot = %s
                      AND status = 'active'
                    """,
                    (user_id, source_bot),
                )
                row = cur.fetchone()
            else:
                cur.execute(
                    """
                    SELECT 1 FROM vip_users
                    WHERE user_id = %s AND paket = %s
                      AND status = 'active' AND end_date > NOW()
                    """,
                    (user_id, paket),
                )
                if cur.fetchone():
                    log.warning(
                        f"[VIP] ⛔ Promo sekali gagal → user_id={user_id}, paket={paket}"
                    )
                    return {
                        "success": False,
                        "reason": "promo_active",
                        "user_id": user_id,
                    }

            # === 4. Hitung start & end date ===
            
            if row:
                existing_start = ensure_aware(row["start_date"], JAKARTA_TZ)
                existing_end = ensure_aware(row["end_date"], JAKARTA_TZ)

                if existing_end is None:
                    raise RuntimeError("EXTEND tanpa expired_lama")

                expired_lama = existing_end

                if existing_end > now_jakarta:
                    # 🔁 EXTEND
                    is_extend = True
                    start_date = existing_start
                    end_date = existing_end + timedelta(days=durasi_hari)
                else:
                    # 🔄 RESET → BARU
                    is_extend = False
                    start_date = now_jakarta
                    end_date = now_jakarta + timedelta(days=durasi_hari)
            else:
                # 🆕 BARU MURNI
                is_extend = False
                start_date = now_jakarta
                end_date = now_jakarta + timedelta(days=durasi_hari)

            # === 5. Upsert ke vip_users ===
            cur.execute(
                """
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
                """,
                (user_id, username, start_date, end_date, paket, source_bot),
            )
            log.info(f"[VIP] 💾 vip_users upsert sukses user_id={user_id}")

            # === 6. Catat ke vip_logs ===
            cur.execute(
                """
                INSERT INTO vip_logs (
                    target_user_id, admin_user_id, paket,
                    basic_days, bonus_days, durasi_hari,
                    is_extend, expired_baru, keterangan,
                    source, source_bot, target_bot, batch_uuid, promo_once
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT ON CONSTRAINT uniq_vip_logs_batch_uuid
                DO NOTHING
                RETURNING id
                """,
                (
                    user_id,
                    admin_id,
                    paket,
                    basic_days,
                    bonus_days,
                    durasi_hari,
                    is_extend,
                    end_date,
                    keterangan,
                    source,
                    source_bot,
                    target_bot,
                    batch_uuid,
                    is_promo_once,
                ),
            )

            row = cur.fetchone()

            if not row:
                log.warning(
                    "[VIP] Duplicate batch ignored user_id=%s batch_uuid=%s",
                    user_id,
                    batch_uuid,
                )
                conn.commit()
                return {
                    "success": True,
                    "duplicate": True,
                    "user_id": user_id,
                    "paket": paket,
                }


            # === 7. Hitung total pembelian user ===
            cur.execute(
                """SELECT COUNT(*) FROM vip_logs WHERE target_user_id = %s""",
                (user_id,),
            )
            purchases = cur.fetchone()["count"]

            if not row:
                log.warning(
                    "[VIP] Duplicate batch ignored user_id=%s batch_uuid=%s",
                    user_id,
                    batch_uuid,
                )

            # === 8. Commit transaksi ===
            conn.commit()
            log.info(f"[VIP] ✅ Sukses {paket} untuk user_id={user_id}")

        # === 9. Return hasil ===

        return {
            "success": True,
            "paket": paket,
            "basic_days": basic_days,
            "bonus_days": bonus_days,
            "durasi_hari": durasi_hari,
            "expired_at": end_date,
            "start_at": start_date,
            "is_new": not is_extend,
            "is_extend": is_extend,          # ✅ WAJIB
            "expired_lama": expired_lama,    # ✅ WAJIB
            "mode": "extend" if is_extend else "baru",  # ✅ WAJIB
            "user_id": user_id,
            "source_bot": source_bot,
            "purchases": purchases,
        }

    except RuntimeError:
        raise

    except errors.UniqueViolation as e:
        log.error(
            f"[VIP] ❌ UniqueViolation → user_id={user_id}, paket={paket}, detail={e}"
        )
        return {"success": False, "reason": "duplicate", "user_id": user_id}

    except Exception as e:
        log.error(
            f"[VIP] ❌ Gagal safe_insert_vip_user → user_id={user_id}, error={e}",
            exc_info=True,
        )
        return {"success": False, "error": str(e), "user_id": user_id}


def activate_vip(
    user_id: int,
    username: str,
    paket: str,
    durasi_hari: int | None = None,
    admin_id: int = 0,
    source: str = "manual",
    keterangan: str = "Aktivasi manual",
    source_bot: str = "drac1n",
    target_bot: str = "drac1n",
):
    """
    Wrapper legacy activate_vip.
    Semua logic inti didelegasikan ke safe_insert_vip_user.
    """

    paket_info = get_vip_package_info(paket)
    if not paket_info:
        return {"success": False, "reason": "invalid_paket"}

    paket_name, basic_days, total_days = paket_info

    # fallback jika caller lama masih kirim durasi_hari
    durasi = durasi_hari or total_days
    bonus_days = max(durasi - basic_days, 0)

    batch_uuid = f"legacy-{admin_id}-{uuid4()}"

    return safe_insert_vip_user(
        user_id=user_id,
        username=username,
        paket=paket_name,
        durasi_hari=durasi,
        basic_days=basic_days,
        bonus_days=bonus_days,
        admin_id=admin_id,
        source=source,
        keterangan=keterangan,
        source_bot=source_bot,
        target_bot=target_bot,
        batch_uuid=batch_uuid,
        is_promo_once=False,
    )

def extend_or_activate_vip(
    user_id: int,
    paket: str,
    admin_id: int,
    username: str = None,
    source_bot: str = "drac1n",
    keterangan: str = "Perpanjangan manual",
    update_user_table: bool = True,
) -> dict:
    """
    Extend atau aktifkan VIP untuk user_id tertentu.
    Cocok untuk perpanjangan manual yang sederhana.
    """
    try:
        now = datetime.now(timezone.utc)

        # Ambil info paket dari DB
        paket_info = get_vip_package_info(paket)
        if not paket_info:
            log.warning(
                f"[EXTEND_OR_ACTIVATE] Paket tidak valid: {paket} user_id={user_id}"
            )
            return {"success": False, "reason": "invalid_paket"}

        paket_name, basic_days, total_days = paket_info
        duration = total_days

        with get_db_cursor() as (cur, conn):
            # Cek existing VIP
            cur.execute(
                """
                SELECT end_date
                FROM vip_users
                WHERE user_id = %s AND source_bot = %s
                ORDER BY end_date DESC
                LIMIT 1
                """,
                (user_id, source_bot),
            )
            row = cur.fetchone()

            has_old_vip = bool(row)
            expired_lama = row["end_date"] if row else None

            if has_old_vip:
                if not expired_lama:
                    raise RuntimeError("EXTEND tanpa expired_lama")
                is_extend = True

            is_extend = False
            if row and row[0]:
                expired_date = ensure_aware(row[0])
                if expired_date > now:
                    new_end = expired_date + timedelta(days=duration)
                    is_extend = True
                    start_date = None
                else:
                    new_end = now + timedelta(days=duration)
                    start_date = now
            else:
                new_end = now + timedelta(days=duration)
                start_date = now

            # Insert/Update VIP
            cur.execute(
                """
                INSERT INTO vip_users (
                    user_id, username, start_date, end_date,
                    paket, status, source_bot, updated_at
                )
                VALUES (%s, %s, %s, %s, %s, 'active', %s, NOW())
                ON CONFLICT (user_id, source_bot) DO UPDATE
                SET end_date = EXCLUDED.end_date,
                    paket = EXCLUDED.paket,
                    username = COALESCE(EXCLUDED.username, vip_users.username),
                    status = 'active',
                    updated_at = NOW()
                """,
                (user_id, username, start_date, new_end, paket_name, source_bot),
            )

            # Log VIP activity
            cur.execute(
                """
                INSERT INTO vip_logs (
                    target_user_id, admin_user_id, paket, durasi_hari,
                    is_extend, expired_baru, keterangan, source_bot
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    user_id,
                    admin_id,
                    paket_name,
                    duration,
                    is_extend,
                    new_end,
                    keterangan,
                    source_bot,
                ),
            )

            # Update tabel users biar konsisten
            if update_user_table:
                table = get_table_name(source_bot)
                if table:
                    cur.execute(
                        f"""
                        UPDATE {table}
                        SET is_vip = TRUE,
                            vip_expired = %s,
                            vip_start = COALESCE(vip_start, %s),
                            vip_purchases = COALESCE(vip_purchases, 0) + 1,
                            updated_at = NOW()
                        WHERE user_id = %s
                        """,
                        (new_end, now, user_id),
                    )

            conn.commit()

        log.info(
            f"[EXTEND_OR_ACTIVATE] ✅ user_id={user_id}, paket={paket_name}, "
            f"expired_at={new_end}, extend={is_extend}"
        )

        return {
            "success": True,
            "is_extend": is_extend,
            "duration": duration,
            "expired_at": new_end,
            "paket": paket_name,
            "user_id": user_id,
        }

    except Exception as e:
        log.error(
            f"[EXTEND_OR_ACTIVATE] ❌ Gagal proses user_id={user_id}: {e}",
            exc_info=True,
        )
        return {"success": False, "reason": str(e), "user_id": user_id}
