def build_welcome_text(user_name, greeting, is_vip=False):
    vip_section = (
        "💎 <b>VIP Member</b>\n"
        "Terima kasih sudah menjadi member VIP.\n"
        "Nikmati semua episode premium tanpa batas.\n\n"
        if is_vip
        else "💎 <b>VIP Member</b>\n"
        "Nonton tanpa batas, akses episode lengkap & premium.\n\n"
    )

    return (
        f"👋 {greeting}, <b>{user_name}</b>!\n"
        f"🏮 Selamat datang di <b>DCSTV • Short Drama</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🎬 <b>Short Drama Pilihan</b>\n"
        f"Kisah singkat penuh emosi, cinta, dan takdir.\n\n"
        f"{vip_section}"
        f"💰 <b>Mau nonton sambil cuan?</b>\n"
        f"Bagikan link kamu, dapatkan komisi dari setiap pembelian VIP.\n"
        f"<i>Tanpa modal. Tanpa ribet.</i>\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📌 <b>Pilih menu di bawah untuk mulai:</b>"
    )
