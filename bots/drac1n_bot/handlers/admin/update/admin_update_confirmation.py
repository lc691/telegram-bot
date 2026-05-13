from pyrogram.enums import ParseMode
from pyrogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from common.utils.admin_state_manager import AdminStateManager
from common.utils.state_helper import cancel_all_states
from configs.logging_setup import log
from db.connect import get_db_cursor


def escape_markdown(text: str) -> str:
    if not text:
        return "-"
    return (
        text.replace("\\", "\\\\")
        .replace("<code>", "\\<code>")
        .replace("_", "\\_")
        .replace("*", "\\*")
        .replace("-", "\\-")
    )


async def handle_admin_update_confirmation(
    client, callback_query: CallbackQuery, state: AdminStateManager
):
    user_id = callback_query.from_user.id
    log.info(f"[ADMIN_UPDATE_CONFIRM] Konfirmasi update dimulai oleh {user_id}")

    try:
        # STEP 1: Ambil data dari state
        admin_data = state.get_temp_json("admin_update_target")
        new_data = state.get_temp_json("admin_update_new_data")

        if not admin_data or not new_data:
            log.warning(
                f"[ADMIN_UPDATE_CONFIRM] Data tidak lengkap untuk user {user_id}"
            )
            await callback_query.message.edit_text(
                "⚠️ Data update tidak ditemukan atau sudah kadaluarsa.",
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
            return

        target_id = admin_data.get("user_id")
        if not target_id:
            log.warning(f"[ADMIN_UPDATE_CONFIRM] user_id kosong dalam admin_data")
            await callback_query.message.edit_text(
                "⚠️ Terjadi kesalahan data internal.", parse_mode=ParseMode.MARKDOWN
            )
            return

        # STEP 2: Cek apakah data berubah
        if admin_data.get("first_name") == new_data.get(
            "first_name"
        ) and admin_data.get("username") == new_data.get("username"):
            log.info(
                f"[ADMIN_UPDATE_CONFIRM] Tidak ada perubahan untuk admin {target_id}"
            )
            await callback_query.message.edit_text(
                "ℹ️ Tidak ada perubahan pada data admin.",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                "🏠 Kembali", callback_data="admin_tools_menu"
                            )
                        ]
                    ]
                ),
                parse_mode=ParseMode.HTML,
            )
            return

        # STEP 3: Update database
        with get_db_cursor() as (cursor, conn):
            cursor.execute(
                """
                UPDATE admins
                SET first_name = %s,
                    username = %s
                WHERE user_id = %s
                """,
                (
                    new_data.get("first_name"),
                    new_data.get("username"),
                    target_id,
                ),
            )
            conn.commit()

        log.info(f"[ADMIN_UPDATE_CONFIRM] Admin {target_id} berhasil diperbarui.")

        first_name_escaped = escape_markdown(new_data.get("first_name"))
        username_display = (
            f"@{new_data.get('username')}" if new_data.get("username") else "-"
        )

        # STEP 4: Tampilkan hasil
        await callback_query.message.edit_text(
            f"✅ Admin berhasil diperbarui:\n\n"
            f"🆔 <code>{target_id}</code>\n"
            f"👤 {first_name_escaped}\n"
            f"🔗 {username_display}",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("🏠 Kembali", callback_data="admin_tools_menu")]]
            ),
        )

    except Exception as e:
        log.exception(f"[ADMIN_UPDATE_CONFIRM] Gagal update admin {user_id}: {e}")
        try:
            await callback_query.message.edit_text(
                "❌ Gagal memperbarui data admin. Silakan coba lagi.",
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
        except Exception as e2:
            log.warning(
                f"[ADMIN_UPDATE_CONFIRM] Gagal tampilkan pesan error fallback: {e2}"
            )

    finally:
        cancel_all_states(user_id)
        try:
            state.clear()
            log.info(f"[ADMIN_UPDATE_CONFIRM] State dibersihkan untuk user {user_id}")
        except Exception as e:
            log.warning(f"[ADMIN_UPDATE_CONFIRM] Gagal clear state: {e}")
