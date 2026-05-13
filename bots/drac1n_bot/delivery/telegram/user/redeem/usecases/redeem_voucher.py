from datetime import datetime

from pyrogram import Client
from pytz import timezone

from common.messaging.notification_group import send_vip_group_announcement
from configs.logging_setup import log
from db.connect import get_db_cursor
from db.vip_users.vip_activation import safe_insert_vip_user

# Zona waktu default (WIB)
WIB = timezone("Asia/Jakarta")


async def redeem_voucher(
    app: Client,
    code: str,
    user_id: int,
    username: str,
    vip_group_id: int,
    actor_id: int | None = None,  # admin yang mengaktifkan (opsional)
):
    """
    Redeem voucher VIP.
    - Jika actor_id None → user redeem sendiri.
    - Jika actor_id diisi → admin redeem untuk user lain.
    """
    try:
        log.info(
            f"[STEP 1] 🔍 Memulai proses redeem voucher '{code}' "
            f"untuk user_id={user_id} (actor={actor_id or 'SELF'})"
        )

        # 1️⃣ Cek voucher
        with get_db_cursor(commit=True) as (cur, _):
            cur.execute(
                """
                SELECT duration_days, is_used, expires_at, created_by
                FROM vip_vouchers
                WHERE code = %s
                FOR UPDATE
                """,
                (code,),
            )
            row = cur.fetchone()

            if not row:
                log.warning(f"[STEP 2] ❌ Voucher {code} tidak ditemukan.")
                return "❌ Kode voucher tidak ditemukan. Pastikan tidak typo ya!"

            duration_days, is_used, expires_at, created_by = row
            now_wib = datetime.now(WIB)

            log.info(
                f"[STEP 2] ✅ Voucher ditemukan: durasi={duration_days} hari, "
                f"is_used={is_used}, expires_at={expires_at}, dibuat_oleh={created_by}"
            )

            # 2️⃣ Validasi voucher
            if is_used:
                log.warning(f"[STEP 3] ⚠️ Voucher {code} sudah digunakan.")
                return "😢 Voucher sudah digunakan oleh orang lain."

            if expires_at and now_wib > expires_at.astimezone(WIB):
                log.warning(f"[STEP 3] ⚠️ Voucher {code} sudah kedaluwarsa.")
                return "⏰ Voucher ini sudah kedaluwarsa."

            # 3️⃣ Tandai voucher sebagai digunakan
            cur.execute(
                """
                UPDATE vip_vouchers
                SET is_used = TRUE, used_at = NOW(), used_by = %s
                WHERE code = %s
                """,
                (user_id, code),
            )
            log.info(
                f"[STEP 4] 🧾 Voucher {code} ditandai terpakai oleh user_id={user_id}"
            )

        # 4️⃣ Tambahkan / perpanjang VIP user
        vip_result = safe_insert_vip_user(
            user_id=user_id,
            username=username or "",
            paket=f"Voucher {duration_days} hari",
            durasi_hari=duration_days,
            keterangan=f"Redeem voucher {code}",
            source="voucher",
            source_bot="drac1n",
            target_bot="drac1n",
            admin_id=actor_id or 0,
            batch_uuid=code,
        )

        if not vip_result["success"]:
            log.error(
                f"[STEP 5] ❌ Gagal aktivasi VIP untuk {user_id}: {vip_result['error']}"
            )
            return f"⚠️ Terjadi kesalahan saat aktivasi VIP: {vip_result['error']}"

        expired_at = vip_result["expired_at"].astimezone(WIB)
        expired_str = expired_at.strftime("%Y-%m-%d %H:%M:%S WIB")

        log.info(
            f"[STEP 5] ✅ VIP berhasil diaktifkan untuk user_id={user_id} "
            f"selama {duration_days} hari (hingga {expired_str})"
        )

        # 5️⃣ Kirim pengumuman ke grup VIP
        try:
            await send_vip_group_announcement(
                app=app,
                chat_id=vip_group_id,
                username=username,
                user_id=user_id,
                paket=f"Voucher {duration_days} hari",
                via_voucher=True,
            )
            log.info(
                f"[STEP 6] 📢 Pengumuman berhasil dikirim ke grup VIP untuk user_id={user_id}"
            )
        except Exception as e:
            log.warning(f"[STEP 6] ⚠️ Gagal kirim pengumuman ke grup VIP: {e}")

        # 6️⃣ Catatan log akhir
        if actor_id:
            log.info(
                f"[STEP 7] 🧑‍💼 Admin {actor_id} menukarkan voucher {code} "
                f"untuk user {user_id} ({username})"
            )
        else:
            log.info(
                f"[STEP 7] 👤 User {user_id} ({username}) berhasil redeem voucher {code}"
            )

        # ✅ Respons akhir ke user
        return (
            f"🎉 Voucher berhasil diaktifkan!\n"
            f"👤 User: {username or user_id}\n"
            f"💎 Durasi: {duration_days} hari\n"
            f"📅 Aktif sampai: {expired_str}"
        )

    except Exception as e:
        log.error(f"[ERROR] 🚨 Gagal redeem voucher {code}: {e}", exc_info=True)
        return "🚨 Terjadi kesalahan internal saat memproses voucher. Coba lagi nanti."
