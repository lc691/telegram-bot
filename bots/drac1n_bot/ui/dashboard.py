from datetime import datetime, timedelta
from typing import Union

import pytz

from pyrogram.enums import ParseMode
from pyrogram.errors import MessageNotModified, QueryIdInvalid
from pyrogram.types import CallbackQuery, Message

from bots.drac1n_bot.keyboard.dashboard_tools import generate_dashboard_markup
from bots.drac1n_bot.utils.text_formatter import format_rupiah
from configs.logging_setup import log
from db.admin.dashboard_stats import get_dashboard_stats

# ========== SIMPLE CACHE (5 MENIT) ==========
_cached_stats = None
_cached_time = None
_CACHE_DURATION = timedelta(minutes=5)


def get_cached_dashboard_stats():
    global _cached_stats, _cached_time
    now = datetime.now()

    if _cached_stats and _cached_time and now - _cached_time < _CACHE_DURATION:
        return _cached_stats

    _cached_stats = get_dashboard_stats()
    _cached_time = now
    return _cached_stats


def generate_dashboard_text(stats: dict) -> str:
    now_str = datetime.now(pytz.timezone("Asia/Jakarta")).strftime(
        "%d %B %Y • %H:%M WIB"
    )

    return (
        f"📊 **Dashboard Admin — Update Terbaru**\n"
        f"🕒 `{now_str}`\n"
        f"━━━━━━━━━━━━━━━━━━━\n\n"
        f"👥 **Total Pengguna:** `{stats['total_users']}`"
        f" _( +{stats['new_users_today']} hari ini )_\n"
        f"  ┗ 🧠 Drac1n: `{stats['users_drac1n']}`\n"
        f"  ┗ 📘 UTBK: `{stats['users_utbk']}`\n"
        f"\n👑 **VIP Aktif:** `{stats['total_vip']}`"
        f" _( {stats['vip_percentage']}% dari total )_\n"
        f"  ┗ 🧠 Drac1n: `{stats['vip_drac1n']}`\n"
        f"  ┗ 📘 UTBK: `{stats['vip_utbk']}`\n"
        f"\n📽️ **Video Diputar:** `{stats['total_plays']}`\n"
        f"📤 **File Terunggah:** `{stats['total_files']}`\n"
        f"\n💰 **Total Donasi:** `{format_rupiah(stats['total_amount'])}`\n"
        f"  ┗ 🎁 Umum: `{format_rupiah(stats['total_donasi'])}`\n"
        f"  ┗ 👑 VIP: `{format_rupiah(stats['total_vip_donation'])}`\n"
        f"\n🧑‍💼 **Admin Aktif:** `{stats['total_admins']}`\n"
        f"\n🔄 **Terakhir diperbarui:** `{now_str}`"
    )


async def _handle_callback(source: CallbackQuery, text: str, markup):
    try:
        await source.answer("✅ Memperbarui dashboard...")
    except QueryIdInvalid:
        log.warning("[send_dashboard] ⚠️ Query ID sudah kadaluarsa (diabaikan)")

    try:
        await source.message.edit_text(
            text, reply_markup=markup, parse_mode=ParseMode.MARKDOWN
        )
    except MessageNotModified:
        log.debug("[send_dashboard] Tidak ada perubahan pada dashboard.")
        await source.answer("✅ Tidak ada perubahan pada dashboard.")
    except Exception as e:
        log.error(f"[send_dashboard] Gagal update dashboard: {e}", exc_info=True)
        try:
            await source.answer("❌ Gagal memperbarui dashboard.")
        except Exception:
            pass


async def _handle_message(source: Message, text: str, markup):
    try:
        await source.reply_text(
            text, reply_markup=markup, parse_mode=ParseMode.MARKDOWN
        )
    except Exception as e:
        log.error(f"[send_dashboard] Gagal kirim dashboard: {e}", exc_info=True)


async def send_dashboard(source: Union[Message, CallbackQuery], is_callback: bool):
    try:
        stats = get_cached_dashboard_stats()
        if not stats:
            if isinstance(source, Message):
                await source.reply_text(
                    "⚠️ Gagal memuat dashboard, silakan hubungi developer."
                )
            return

        text = generate_dashboard_text(stats)
        markup = generate_dashboard_markup()

        if is_callback and isinstance(source, CallbackQuery):
            await _handle_callback(source, text, markup)
        elif isinstance(source, Message):
            await _handle_message(source, text, markup)
        else:
            log.warning(f"[send_dashboard] Tipe source tidak dikenali: {type(source)}")

    except Exception as e:
        log.error(f"[send_dashboard] Exception umum: {e}", exc_info=True)
