from typing import Final

UpsellKey = tuple[str, str]

UPSELL_COPY: Final[dict[UpsellKey, str]] = {
    # 1H → 3H (soft)
    ("1hari", "3hari"): (
        "💡 Tanggung kalau cuma 1 hari\n\n"
        "💎 <b>VIP 3 Hari lebih praktis</b>\n"
        "📉 Lebih hemat per hari\n"
        "🧠 Tidak perlu beli ulang besok"
    ),
    # 1H → 7H (main upsell)
    ("1hari", "7hari"): (
        "💡 Sedikit lagi jauh lebih untung\n\n"
        "💎 <b>VIP 7 Hari pilihan aman</b>\n"
        "📉 Harga per hari jauh lebih murah\n"
        "🧠 Lebih tenang, tidak buru-buru"
    ),
    # 3H → 7H
    ("3hari", "7hari"): (
        "💡 Tinggal naik sedikit\n\n"
        "💎 <b>VIP 7 Hari cocok untuk lanjut nonton</b>\n"
        "📉 Lebih hemat per hari\n"
        "🧠 Tidak repot beli ulang"
    ),
    # 7H → 10H (JEMBATAN)
    ("7hari", "10hari"): (
        "💡 Banyak yang naik ke sini\n\n"
        "💎 <b>VIP 10 Hari lebih lega</b>\n"
        "📉 Selisih kecil, durasi lebih panjang\n"
        "🧠 Cocok kalau 7 hari terasa kurang"
    ),
    # 10H → 15H
    ("10hari", "15hari"): (
        "💡 Sedikit lagi lebih hemat\n\n"
        "💎 <b>VIP 15 Hari lebih seimbang</b>\n"
        "📉 Harga per hari lebih murah\n"
        "🧠 Aman untuk 2 minggu"
    ),
    # 15H → 30H (BEST VALUE)
    ("15hari", "30hari"): (
        "🔥 Rekomendasi Terbaik\n\n"
        "👑 <b>VIP 30 Hari = Best Value</b>\n"
        "📉 Harga per hari paling murah\n"
        "🚀 Sekali bayar, aman sebulan"
    ),
}
