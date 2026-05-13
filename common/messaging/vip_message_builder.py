import html

from datetime import datetime


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
    Membuat pesan aktivasi VIP untuk user (format HTML).
    """

    # =====================================================
    # Step 1: Format tanggal
    # =====================================================
    start_str = vip_start.strftime("%d %b %Y %H:%M") if vip_start else "Tidak diketahui"
    end_str = vip_end.strftime("%d %b %Y %H:%M") if vip_end else "Tidak diketahui"

    # =====================================================
    # Step 2: Escape agar aman di HTML
    # =====================================================
    first_name_safe = html.escape(first_name)
    username_safe = html.escape(username) if username else None
    paket_safe = html.escape(paket)

    # =====================================================
    # Step 3: Tentukan status aktivasi
    # =====================================================
    if is_promo_once:
        status_label = "Promo Spesial 🎁"
    elif is_extend:
        status_label = "Perpanjangan ♻️"
    else:
        status_label = "Aktivasi Baru 🆕"

    # =====================================================
    # Step 4: Susun isi pesan utama
    # =====================================================
    lines = [
        f"🎉 Selamat <b>{first_name_safe}</b>!",
        (
            f"👤 User: @{username_safe}"
            if username_safe
            else f"🆔 ID: <code>{user_id}</code>"
        ),
        f"📦 Paket: <code>{paket_safe}</code>",
        f"🕒 Aktif: {start_str} → {end_str}",
        f"🔁 Status: {status_label}",
        f"⭐ Pembelian ke-{purchases}",
    ]

    if bonus > 0:
        lines.append(f"🎁 Bonus Hari: +{bonus}")

    # =====================================================
    # Step 5: Tambahkan pemisah & hashtag branding
    # =====================================================
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━")
    hashtags = "#VIP #Streaming"
    if is_promo_once:
        hashtags += " #PromoOnce"
    elif is_extend:
        hashtags += " #Extend"
    else:
        hashtags += " #Baru"
    hashtags += f" #VIP_{paket_safe.replace(' ', '')}"
    lines.append(hashtags)

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
