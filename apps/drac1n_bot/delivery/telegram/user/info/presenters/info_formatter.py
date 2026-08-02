from .info_helpers import format_wib, sisa_waktu


def format_info_text(
    *,
    user_id: int,
    username: str | None,
    first_name: str | None,
    is_vip: bool,
    vip_start,
    vip_expired,
    is_private: bool,
) -> str:

    title = (
        "👤 Info Pengguna"
        if is_private
        else "👥 Info Member"
    )

    display_name = (
        username
        or first_name
        or "Pengguna Telegram"
    )

    status_icon = "👑" if is_vip else "💤"

    status_text = (
        "✅ <b>VIP Aktif</b>"
        if is_vip
        else "❌ <b>Tidak VIP</b>"
    )

    lines = [
        f"<b>{title}</b>",
        "═══════✦✧✦═══════\n",
        f"👤 <b>Nama</b> :</b> {display_name}",
        f"🆔 <b>ID       :</b> <code>{user_id}</code>\n",

        f"{status_icon} <b>Status VIP</b>",
        f"└─ 💎<b>Status :</b> {status_text}",
    ]

    if is_vip:
        lines.extend([
            f"├─ 📆 <b>Mulai    :</b> <code>{format_wib(vip_start)}</code>",
            f"├─ 🛑 <b>Berakhir :</b> <code>{format_wib(vip_expired)}</code>",
            f"└─ ⏳ <b>Sisa     :</b> <code>{sisa_waktu(vip_expired)}</code>",
        ])

    lines.extend([
        "═══════✦✧✦═══════\n",
        "💬 Gunakan perintah /status untuk detail lebih lanjut.",
    ])

    return "\n".join(lines)