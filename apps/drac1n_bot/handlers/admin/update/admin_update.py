from pyrogram import Client
from pyrogram.enums import ParseMode
from pyrogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from shared.utils.admin_state_manager import AdminStateManager
from shared.utils.state_helper import cancel_all_states
from configs.logging_setup import log
from database.connection import get_dict_cursor


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


# === STEP 1: Mulai proses update admin ===
async def admin_update_start(client: Client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    log.info(f"[ADMIN_UPDATE_START] Dimulai oleh {user_id}")

    try:
        cancel_all_states(user_id)
        state = AdminStateManager(user_id)
        state.set_step("regular_step", "awaiting_admin_id_for_update")

        await callback_query.message.edit_text(
            "🛠 Masukkan `user_id` admin yang ingin diubah datanya:",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("❌ Batal", callback_data="admin_tools_menu")]]
            ),
            parse_mode=ParseMode.HTML,
        )
    except Exception as e:
        log.error(f"[ADMIN_UPDATE_START] Gagal mulai proses: {e}", exc_info=True)
        try:
            await callback_query.answer("❌ Gagal memulai proses update.")
        except Exception as notify_err:
            log.warning(
                f"[ADMIN_UPDATE_START] Gagal kirim notifikasi error: {notify_err}"
            )


# === STEP 2: Input user_id admin yang ingin diubah ===
async def handle_admin_update_step(
    app: Client, message: Message, admin_state: AdminStateManager
):
    user_id = message.from_user.id

    if admin_state.get_step("regular_step") != "awaiting_admin_id_for_update":
        log.debug(f"[ADMIN_UPDATE] Step tidak cocok untuk {user_id}")
        return

    user_input = message.text.strip()
    try:
        target_id = int(user_input)
        if target_id <= 0:
            raise ValueError
    except ValueError:
        await message.reply_text("❌ ID harus berupa angka positif.")
        return

    try:
        # Ambil data admin dari DB
        with get_dict_cursor() as (cursor, _):
            cursor.execute("SELECT * FROM admins WHERE user_id = %s", (target_id,))
            admin = cursor.fetchone()

        if not admin:
            log.info(f"[ADMIN_UPDATE] Admin {target_id} tidak ditemukan di DB")
            await message.reply_text("⚠️ User tersebut belum menjadi admin.")
            return

        # Ambil data Telegram terkini (jika bisa)
        try:
            tg_user = await app.get_users(target_id)
            first_name = tg_user.first_name or admin.get("first_name", "Tanpa Nama")
            username = tg_user.username or admin.get("username")
        except Exception as e:
            log.warning(
                f"[ADMIN_UPDATE] Gagal ambil data Telegram untuk {target_id}: {e}"
            )
            first_name = admin.get("first_name", "Unknown")
            username = admin.get("username")

        # Simpan ke state untuk konfirmasi
        admin_state.set_temp_json(
            "admin_update_target",
            {
                "user_id": target_id,
                "first_name": admin.get("first_name", "Unknown"),
                "username": admin.get("username", None),
            },
        )

        admin_state.set_temp_json(
            "admin_update_new_data",
            {
                "first_name": first_name,
                "username": username,
            },
        )

        admin_state.set_step("regular_step", "confirm_update_admin")
        log.info(f"[ADMIN_UPDATE] Menunggu konfirmasi perubahan untuk {target_id}")

        # Tampilkan konfirmasi ke admin
        first_name_escaped = escape_markdown(first_name)
        username_display = f"@{username}" if username else "-"

        await message.reply_text(
            f"⚠️ Yakin ingin **mengubah data** admin berikut?\n\n"
            f"🆔 `{target_id}`\n"
            f"👤 {first_name_escaped}\n"
            f"🔗 {username_display}",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "✅ Ya",
                            callback_data=f"admin_update_confirm_yes_{target_id}",
                        ),
                        InlineKeyboardButton(
                            "❌ Batal", callback_data="admin_tools_menu"
                        ),
                    ]
                ]
            ),
            parse_mode=ParseMode.HTML,
        )

    except Exception as e:
        log.error(
            f"[ADMIN_UPDATE] Gagal proses update admin {target_id}: {e}", exc_info=True
        )
        await message.reply_text("❌ Terjadi kesalahan saat mengambil data admin.")
