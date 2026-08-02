import html

from datetime import datetime
from zoneinfo import ZoneInfo


WIB = ZoneInfo("Asia/Jakarta")


def _format_wib(dt: datetime | None) -> str:
    """
    Format datetime ke WIB.
    """

    if not dt:
        return "Tidak diketahui"

    # naive datetime diasumsikan UTC
    if dt.tzinfo is None:
        dt = dt.replace(
            tzinfo=ZoneInfo("UTC")
        )

    dt = dt.astimezone(WIB)

    return dt.strftime("%d %b %Y %H:%M WIB")


def generate_vip_message_to_user(
    first_name: str,
    username: str | None,
    user_id: int,
    paket: str,
    vip_start: datetime | None,
    vip_end: datetime | None,
    *,
    is_extend: bool = False,
    is_promo_once: bool = False,
    purchases: int = 1,
    bonus: int = 0,
) -> str:
    """
    Generate pesan aktivasi VIP untuk user.
    """

    # =====================================================
    # STEP 1 — Format datetime
    # =====================================================

    start_str = _format_wib(vip_start)
    end_str = _format_wib(vip_end)

    # =====================================================
    # STEP 2 — Escape HTML
    # =====================================================

    first_name_safe = html.escape(first_name)
    paket_safe = html.escape(paket)

    username_safe = (
        html.escape(username)
        if username
        else None
    )

    # =====================================================
    # STEP 3 — Status label
    # =====================================================

    if is_promo_once:
        status_label = "Promo Spesial 🎁"

    elif is_extend:
        status_label = "Perpanjangan ♻️"

    else:
        status_label = "Aktivasi Baru 🆕"

    # =====================================================
    # STEP 4 — User identity
    # =====================================================

    if username_safe:
        user_identity = f"👤 <b>User:</b> @{username_safe}"
    else:
        user_identity = f"🆔 <b>User ID:</b> <code>{user_id}</code>"

    # =====================================================
    # STEP 5 — Build message
    # =====================================================

    lines = [
        "🔥 <b>VIP Berhasil Diaktifkan</b> 🔥",
        "",
        f"Halo <b>{first_name_safe}</b> 👋",
        "🎉 Selamat! akses VIP kamu sekarang sudah aktif.",
        "",
        user_identity,
        "",
        "═══════✦✧✦═══════",
        "📄 <b>Detail VIP Kamu</b>",
        "",
        f"├─ 📦 <b>Paket VIP  :</b> <code>{paket_safe}</code>",
        f"├─ ⏳ <b>Aktif Dari :</b> <code>{start_str}</code>",
        f"└─ 🛑 <b>Berakhir   :</b> <code>{end_str}</code>",
        "",
        f"🔁 <b>Status</b> : {status_label}",
        f"⭐ <b>Pembelian</b> : ke-{max(1, purchases)}",
    ]

    if bonus > 0:
        lines.append(
            f"🎁 <b>Bonus Hari</b> : +{bonus}"
        )
    # =====================================================
    # STEP 6 — Footer
    # =====================================================

    lines.extend([
        "═══════✦✧✦═══════",
        "",
        f"#VIP #Streaming #VIP_{paket_safe.replace(' ', '')}",
    ])

    return "\n".join(lines)


def generate_vip_message_to_admin(
    first_name: str,
    username: str | None,
    user_id: int,
    paket: str,
    purchases: int,
    is_extend: bool,
    is_promo_once: bool = False,
) -> str:
    """
    Membuat pesan notifikasi aktivasi VIP untuk admin (format MarkdownV2).
    """

    # =====================================================
    # Step 1: Escape agar aman
    # =====================================================
    first_name_esc = html.escape(first_name)
    username_str = f"@{html.escape(username)}" if username else "—"
    paket_clean = html.escape(paket.upper())

    # =====================================================
    # Step 2: Tentukan prefix
    # =====================================================
    if is_promo_once:
        prefix = "🎁 PromoOnce"
    elif is_extend:
        prefix = "♻️ Diperpanjang"
    else:
        prefix = "🆕 Baru"

    # =====================================================
    # Step 3: Susun isi pesan
    # =====================================================
    return (
        f"🎫 **VIP {prefix}**\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 **{first_name_esc}** ({username_str})\n"
        f"🆔 **User ID:** `{user_id}`\n"
        f"📦 Paket: `{paket_clean}`\n"
        f"⭐ Pembelian ke-{purchases}\n"
        f"━━━━━━━━━━━━━━━━━━━━"
    )
