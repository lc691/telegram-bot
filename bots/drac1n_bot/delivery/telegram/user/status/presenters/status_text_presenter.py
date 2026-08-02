from ..usecases.date_formatter import format_date
from ..usecases.akses_policy import build_akses_harian


def format_status_text(
    user_id: int,
    data: dict,
    is_admin: bool,
    lang_code: str = "id",
) -> str:
    akses_str = (
        "♾️ Tak terbatas"
        if is_admin or data.get("is_vip")
        else build_akses_harian(data, is_admin, lang_code)
    )

    subscription_str = (
        "✅ Admin" if is_admin else "✅ Aktif" if data.get("is_vip") else "❌ Tidak"
    )

    kode = f"daftar_short_{user_id}"

    return (
        "🔥 <b>Upgrade ke VIP Sekarang!</b> 🔥\n"
        "Nikmati akses eksklusif tanpa batas, tonton video favoritmu tanpa hambatan! 🚀\n\n"
        "✅ <b>Status VIP Kamu</b>\n"
        f"═══════✦✧✦═══════\n\n"
        f"👤 <b>User ID:</b> <code>{user_id}</code>\n"
        f"🔗 <b>Kode VIP:</b> <code>{kode}</code>\n\n"
        f"🎞️ <b>Akses Hari Ini:</b>\n└─ {akses_str}\n"
        f"💳 <b>Subscription:<b>\n"
        f"└─{subscription_str}\n\n"
        "📄 <b>Detail VIP Kamu:</b>\n"
        f"├─ ⏳ <b>Aktif dari :</b>\n<code>{format_date(data.get('vip_start'), lang_code)}</code>\n"
        f"└─ 🛑 <b>Berakhir   :</b>\n<code>{format_date(data.get('vip_expired'), lang_code)}</code>\n"
        f"═══════✦✧✦═══════\n\n"
        f"⭐️ <b>Jumlah Pembelian VIP Ke:</b> <code>{data.get('purchases', 0)}</code> Pembelian\n"
        "💎 <b>Gabung VIP Sekarang!</b> Ketik /vip untuk upgrade ke VIP dan dapatkan lebih banyak keuntungan! 🎉"
    )
