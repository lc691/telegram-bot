from pyrogram import Client
from pyrogram.enums import ParseMode
from pyrogram.types import Message

from shared.utils.admin_state_manager import AdminStateManager
from configs.logging_setup import log
from database.connection import get_db_cursor


async def handle_add_source_step(
    client: Client, message: Message, admin_state: AdminStateManager
) -> bool:
    user_id = message.from_user.id
    text = message.text.strip()

    step = admin_state.get_step("regular_step")
    log.info(f"[ADMIN_FLOW] Step aktif: {step} oleh {user_id}")

    if step == "awaiting_source_code":
        code = text.upper()

        if not code:
            await message.reply_text("⚠️ Kode tidak boleh kosong. Masukkan ulang.")
            return True

        with get_db_cursor() as (cursor, conn):
            cursor.execute("SELECT 1 FROM request_sources WHERE code = %s", (code,))
            exists = cursor.fetchone()

        if exists:
            await message.reply_text("⚠️ Kode source sudah ada. Masukkan kode lain.")
            return True

        admin_state.set_temp("new_source_code", code)
        admin_state.set_step("regular_step", "awaiting_source_label")
        await message.reply_text(
            f"✅ Kode diterima: <b>{code}</b>\n\nSekarang masukkan label source:",
            parse_mode=ParseMode.HTML,
        )
        return True

    if step == "awaiting_source_label":
        label = text
        code = admin_state.get_temp("new_source_code")

        if not label:
            await message.reply_text("⚠️ Label tidak boleh kosong. Masukkan ulang.")
            return True

        try:
            with get_db_cursor() as (cursor, conn):
                cursor.execute(
                    "INSERT INTO request_sources (code, label) VALUES (%s, %s)",
                    (code, label),
                )
                conn.commit()
                log.info(
                    f"[ADMIN_FLOW] Source baru ditambahkan: code={code}, label={label}"
                )

            await message.reply_text(
                f"✅ Source <b>{label}</b> berhasil ditambahkan!",
                parse_mode=ParseMode.HTML,
            )
        except Exception as e:
            log.exception(f"[ADMIN_FLOW] Gagal insert source: {e}")
            await message.reply_text("❌ Terjadi error saat menyimpan ke database.")
        finally:
            admin_state.clear()
        return True

    return False  # Jika step tidak cocok, return False
