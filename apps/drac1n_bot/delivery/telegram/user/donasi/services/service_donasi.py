import uuid

from pyrogram import Client
from pyrogram.enums import ParseMode
from pyrogram.types import CallbackQuery

from shared.templates.donasi_pesan import pesan_pink, pesan_trakteer
from shared.utils.callback_helpers import safe_answer
from configs.logging_setup import log
from database.donasi_management import save_token_for_user


def generate_donasi_token() -> str:
    try:
        return str(uuid.uuid4()).replace("-", "")[:10]
    except Exception as e:
        log.error(f"[DONASI_TOKEN] ❌ Gagal menghasilkan token: {e}")
        return "TOKEN_ERR"


async def handle_donasi_metode(client: Client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id

    try:
        metode = callback_query.data.split("_", 1)[1]
        token = generate_donasi_token()

        if token == "TOKEN_ERR":
            await callback_query.message.reply_text("❌ Gagal membuat token donasi.")
            return

        try:
            save_token_for_user(user_id, token, metode)
        except Exception as e:
            log.error(f"[DONASI] ❌ Gagal menyimpan token DB: {e}")
            await callback_query.message.reply_text(
                "❌ Gagal menyimpan token ke database."
            )
            return

        # Tentukan isi pesan berdasarkan metode
        try:
            if metode == "trakteer":
                instruksi = pesan_trakteer(token)
            elif metode == "pink":
                instruksi = pesan_pink(token)
            else:
                log.warning(f"[DONASI] ⚠️ Metode tidak dikenal: {metode}")
                instruksi = "❌ Metode donasi tidak dikenali."
        except Exception as e:
            log.error(f"[DONASI_MSG] ❌ Gagal buat instruksi: {e}")
            instruksi = "❌ Terjadi kesalahan dalam membuat instruksi donasi."

        # Jawab interaksi (callback)
        await safe_answer(callback_query)

        # Kirim instruksi ke user dengan edit pesan
        await callback_query.message.edit_text(
            instruksi,
            parse_mode=ParseMode.HTML,
        )

        log.info(f"[DONASI] ✅ Instruksi dikirim ke user {user_id} (metode: {metode})")

    except Exception as e:
        log.error(f"[DONASI] ❌ Kesalahan umum: {e}", exc_info=True)
        try:
            await callback_query.message.reply_text(
                "❌ Terjadi kesalahan saat memproses permintaan donasi."
            )
        except Exception as e:
            log.warning(f"[DONASI] ❌ Gagal reply fallback: {e}")
