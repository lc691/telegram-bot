from pyrogram import Client
from pyrogram.enums import ParseMode
from pyrogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from common.utils.admin_state_manager import AdminStateManager
from common.utils.state_helper import cancel_all_states
from configs.logging_setup import log
from db.connect import get_db_cursor


def escape_markdown(text: str) -> str:
    if not text:
        return "-"
    return (
        text.replace("\\", "\\\\")
        .replace("`", "\\`")
        .replace("_", "\\_")
        .replace("*", "\\*")
        .replace("-", "\\-")
    )


# === STEP 1: Inisiasi proses hapus admin ===
async def admin_remove_start(client: Client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    log.info(f"[ADMIN_REMOVE] Start proses hapus oleh admin {user_id}")

    try:
        cancel_all_states(user_id)
        state = AdminStateManager(user_id)
        state.set_step("regular_step", "awaiting_admin_id_for_remove")

        await callback_query.message.edit_text(
            "🗑️ Silakan masukkan <b>user_id</b> admin yang ingin dihapus.",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("❌ Batal", callback_data="admin_tools_menu")]]
            ),
            parse_mode=ParseMode.HTML,
        )
        log.info(f"[ADMIN_REMOVE] Prompt input user_id dikirim ke {user_id}")

    except Exception as e:
        log.exception(f"[ADMIN_REMOVE] Gagal memulai proses: {e}")
        try:
            await callback_query.message.edit_text(
                "⚠️ Gagal memulai proses hapus admin. Silakan coba lagi.",
                parse_mode=ParseMode.HTML,
            )
        except Exception as e2:
            log.warning(f"[ADMIN_REMOVE] Gagal edit pesan fallback: {e2}")


# === STEP 2: Proses input user_id untuk dihapus ===
async def handle_admin_remove_step(
    app: Client, message: Message, admin_state: AdminStateManager
):
    user_id = message.from_user.id
    input_text = message.text.strip()
    log.info(f"[ADMIN_REMOVE] Input dari {user_id}: {input_text}")

    try:
        if admin_state.get_step("regular_step") != "awaiting_admin_id_for_remove":
            log.warning(f"[ADMIN_REMOVE] Step tidak sesuai, abaikan.")
            return

        # Validasi angka
        try:
            target_id = int(input_text)
        except ValueError:
            await message.reply_text("❌ ID harus berupa angka.")
            return

        # Ambil data admin dari DB
        with get_db_cursor() as (cursor, _):
            cursor.execute(
                "SELECT first_name, username FROM admins WHERE user_id = %s",
                (target_id,),
            )
            admin = cursor.fetchone()

        if not admin:
            await message.reply_text("⚠️ Admin tidak ditemukan.")
            log.info(f"[ADMIN_REMOVE] Admin {target_id} tidak ditemukan.")
            return

        first_name = escape_markdown(admin[0]) or "Tanpa Nama"
        username = admin[1] or "-"
        username_display = f"@{username}" if username != "-" else "-"

        # Simpan ke state untuk konfirmasi
        admin_state.set_temp_json(
            "remove_admin",
            {
                "user_id": target_id,
                "first_name": admin[0],
                "username": username,
            },
        )
        admin_state.set_step("regular_step", "confirm_remove_admin")

        await message.reply_text(
            f"⚠️ Yakin ingin menghapus admin berikut?\n\n"
            f"🆔 `{target_id}`\n"
            f"👤 {first_name}\n"
            f"🔗 {username_display}",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "✅ Ya",
                            callback_data=f"admin_remove_confirm_yes_{target_id}",
                        ),
                        InlineKeyboardButton(
                            "❌ Tidak",
                            callback_data=f"admin_remove_confirm_no_{target_id}",
                        ),
                    ]
                ]
            ),
            parse_mode=ParseMode.HTML,
        )
        log.info(
            f"[ADMIN_REMOVE] Konfirmasi hapus dikirim ke {user_id} untuk target {target_id}"
        )

    except Exception as e:
        log.exception(f"[ADMIN_REMOVE] Error saat proses input: {e}")
        try:
            await message.reply_text(
                "❌ Terjadi kesalahan internal saat memproses permintaan."
            )
        except Exception as e2:
            log.warning(f"[ADMIN_REMOVE] Gagal kirim fallback reply: {e2}")
