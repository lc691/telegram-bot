from .info_helpers import format_wib, sisa_waktu


def format_info_text(
    *,
    user_id: int,
    username: str,
    is_vip: bool,
    vip_start,
    vip_expired,
    is_private: bool,
) -> str:
    status_icon = "👑" if is_vip else "💤"
    status_text = "✅ <b>Aktif</b>" if is_vip else "❌ Tidak aktif"

    text = (
        f"<b>👤 {'Info Pengguna' if is_private else 'Info Member'}</b>\n"
        f"━━━━━━━━━━━━━━━\n"
        f"🆔 <b>ID:</b> <code>{user_id}</code>\n"
        f"📛 <b>Username:</b> {username}\n"
        f"━━━━━━━━━━━━━━━\n"
        f"{status_icon} <b>Status VIP</b>\n"
        f"• Status: {status_text}\n"
    )

    if is_vip:
        text += (
            f"• Mulai: <code>{format_wib(vip_start)}</code>\n"
            f"• Berakhir: <code>{format_wib(vip_expired)}</code>\n"
            f"• ⏳ Sisa: <code>{sisa_waktu(vip_expired)}</code>\n"
        )

    text += (
        "━━━━━━━━━━━━━━━\n"
        "💬 Gunakan perintah <code>/vip</code> untuk detail lebih lanjut."
    )

    return text
