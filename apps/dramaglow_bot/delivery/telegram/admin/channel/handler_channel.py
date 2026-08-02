from pyrogram import Client, filters
from pyrogram.enums import ParseMode
from pyrogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from apps.dramaglow_bot.delivery.telegram.user.services.channel_repository import (
    delete_required_channel,
    load_required_channels,
    validate_required_channels,
)
from apps.dramaglow_bot.utils.channel_markup_factory import (
    generate_channel_list_markup,
    generate_channel_markup,
)
from configs.logging_setup import log
from database.chanel_management import add_user, discard_user


def register_channel_handlers(app: Client):
    # ======================= Tampilkan daftar channel wajib ========================
    @app.on_callback_query(filters.regex("list_required_channels"))
    async def list_required_channels(client: Client, cq: CallbackQuery):
        try:
            channels = load_required_channels()
            if not channels:
                log.info("[CHANNEL] Tidak ada channel wajib terdaftar.")
                await cq.message.edit_text(
                    "🚫 Belum ada channel yang ditambahkan.",
                    reply_markup=generate_channel_markup(),
                )
                return

            text = "**📄 Daftar Channel Wajib:**\n\n"
            for i, ch in enumerate(channels, 1):
                text += f"{i}. <code>{ch['username']}</code>\n👤 oleh <code>{ch['added_by']}</code>\n🕒 {ch['added_at']}\n\n"

            await cq.message.edit_text(
                text,
                parse_mode=ParseMode.HTML,
                reply_markup=generate_channel_list_markup(channels),
            )
            log.info(f"[CHANNEL] Menampilkan {len(channels)} channel wajib.")
        except Exception as e:
            log.exception(f"[CHANNEL] Gagal menampilkan daftar channel: {e}")
            await cq.answer("❌ Gagal menampilkan daftar.", show_alert=True)

    # ======================= Cek status channel bot saat ini ========================
    @app.on_callback_query(filters.regex("check_channels"))
    async def check_channels(client: Client, cq: CallbackQuery):
        try:
            await cq.answer("⏳ Memeriksa channel...")
            results = await validate_required_channels(client)

            text = "**📡 Status Channel:**\n\n"
            for username, status, title in results:
                if status:
                    text += f"✅ <code>{username}</code> — {title}\n"
                else:
                    text += f"❌ <code>{username}</code> — Tidak bisa diakses\n"

            await cq.message.edit_text(
                text,
                parse_mode=ParseMode.HTML,
                reply_markup=generate_channel_markup(),
            )
            log.info(f"[CHANNEL] Status channel diperiksa, total={len(results)}")
        except Exception as e:
            log.exception(f"[CHANNEL] Gagal memeriksa status channel: {e}")
            await cq.answer("❌ Terjadi kesalahan saat memeriksa.", show_alert=True)

    # ======================= Mulai proses tambah channel ========================
    @app.on_callback_query(filters.regex("add_required_channel"))
    async def start_add_channel(client: Client, cq: CallbackQuery):
        try:
            add_user(cq.from_user.id)
            await cq.message.edit_text(
                "Kirim username channel yang ingin ditambahkan, contoh: <code>@channelbaru</code>",
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                "❌ Batal", callback_data="cancel_add_channel"
                            )
                        ]
                    ]
                ),
            )
            log.info(f"[CHANNEL] Admin {cq.from_user.id} mulai tambah channel.")
        except Exception as e:
            log.exception(f"[CHANNEL] Gagal memulai tambah channel: {e}")
            await cq.answer("❌ Gagal memulai proses.", show_alert=True)

    # ======================= Batalkan tambah channel ========================
    @app.on_callback_query(filters.regex("cancel_add_channel"))
    async def cancel_add(client: Client, cq: CallbackQuery):
        try:
            discard_user(cq.from_user.id)
            await cq.message.edit_text(
                "👤 Menu Channel Tools:",
                parse_mode=ParseMode.HTML,
                reply_markup=generate_channel_markup(),
            )
            log.info(f"[CHANNEL] Admin {cq.from_user.id} membatalkan tambah channel.")
        except Exception as e:
            log.exception(f"[CHANNEL] Gagal membatalkan proses tambah: {e}")
            await cq.answer("❌ Gagal membatalkan.", show_alert=True)

    # ======================= Hapus channel dari daftar ========================
    @app.on_callback_query(filters.regex(r"delete_channel:(.+)"))
    async def delete_channel(client: Client, cq: CallbackQuery):
        try:
            username = cq.data.split(":")[1]
            delete_required_channel(username)
            await cq.answer("✅ Channel dihapus.")
            log.info(f"[CHANNEL] Channel {username} dihapus oleh {cq.from_user.id}")
            await list_required_channels(client, cq)  # Refresh list
        except Exception as e:
            log.exception(f"[CHANNEL] Gagal menghapus channel: {e}")
            await cq.answer("❌ Gagal menghapus channel.", show_alert=True)
