from pyrogram import Client
from pyrogram.enums import ParseMode
from pyrogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from shared.utils.admin_state_manager import AdminStateManager
from configs.logging_setup import log
from database.connection import get_db_cursor


# === STEP 1: Callback "admin_add_start" ===
async def admin_add_start(client: Client, callback_query: CallbackQuery):
    admin_id = callback_query.from_user.id
    state = AdminStateManager(admin_id)

    try:
        state.set_step("regular_step", "awaiting_admin_id_for_add")

        await callback_query.message.edit_text(
            "📥 Silakan masukkan <b>user_id</b> admin yang ingin ditambahkan.",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("❌ Batal", callback_data="admin_tools_menu")]]
            ),
            parse_mode=ParseMode.HTML,
        )
        await callback_query.answer()
        log.info(f"[ADMIN_ADD] Admin {admin_id} memulai proses tambah admin.")
    except Exception as e:
        log.exception(f"[ADMIN ADD START] Gagal mulai proses tambah admin: {e}")
        await callback_query.answer("❌ Gagal memulai proses.", show_alert=True)


# === STEP 2: Handler teks setelah memasukkan user_id ===
async def handle_regular_step(
    app: Client, message: Message, admin_state: AdminStateManager
):
    if admin_state.get_step("regular_step") != "awaiting_admin_id_for_add":
        return  # Bukan alur ini

    try:
        user_input = message.text.strip()
        try:
            target_id = int(user_input)
        except ValueError:
            await message.reply_text("❌ User ID harus berupa angka.")
            return

        # STEP 3: Cek apakah user_id sudah jadi admin
        with get_db_cursor() as (cursor, _):
            cursor.execute("SELECT 1 FROM admins WHERE user_id = %s", (target_id,))
            if cursor.fetchone():
                try:
                    tg_user = await app.get_users(target_id)
                    first_name = tg_user.first_name or "Tanpa Nama"
                    username = tg_user.username or "-"
                except Exception:
                    first_name = "Unknown"
                    username = "-"

                await message.reply_text(
                    f"⚠️ User tersebut sudah terdaftar sebagai admin:\n\n"
                    f"🆔 <code>{target_id}</code>\n"
                    f"👤 {first_name}\n"
                    f"🔗 @{username}",
                    reply_markup=InlineKeyboardMarkup(
                        [
                            [
                                InlineKeyboardButton(
                                    "🔙 Kembali", callback_data="admin_tools_menu"
                                )
                            ]
                        ]
                    ),
                    parse_mode=ParseMode.HTML,
                )
                log.info(f"[ADMIN_ADD] User {target_id} sudah menjadi admin.")
                return

        # STEP 4: Ambil info user Telegram
        try:
            tg_user = await app.get_users(target_id)
            first_name = tg_user.first_name or "Tanpa Nama"
            username = tg_user.username or "-"
        except Exception as e:
            log.warning(f"[ADMIN GET USER] Tidak bisa ambil info user {target_id}: {e}")
            first_name = "Unknown"
            username = "-"

        # STEP 5: Simpan sementara & lanjut ke konfirmasi
        admin_state.set_temp_json(
            "new_admin",
            {
                "user_id": target_id,
                "first_name": first_name,
                "username": username,
            },
        )
        admin_state.set_step("regular_step", "confirm_add_admin")

        await message.reply_text(
            f"🆕 Konfirmasi tambah admin:\n\n"
            f"🆔 <code>{target_id}</code>\n"
            f"👤 {first_name}\n"
            f"🔗 @{username}",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "✅ Ya", callback_data=f"admin_add_confirm_yes_{target_id}"
                        ),
                        InlineKeyboardButton(
                            "❌ Batal", callback_data="admin_add_confirm_no_0"
                        ),
                    ]
                ]
            ),
            parse_mode=ParseMode.HTML,
        )
        log.info(f"[ADMIN_ADD] Konfirmasi tambah admin untuk user {target_id}")

    except Exception as e:
        log.exception(f"[ADMIN HANDLE REGULAR STEP] Gagal proses input: {e}")
        await message.reply_text("❌ Terjadi kesalahan saat memproses user ID.")
