from typing import Final

UpsellKey = tuple[str, str]

UPSELL_COPY: Final[dict[UpsellKey, str]] = {
    # 1H → 3H
    ("1hari", "3hari"): (
        "💡 Biar tidak cepat habis\n\n"
        "💎 <b>VIP 3 Hari lebih nyaman</b>\n"
        "📉 Lebih hemat per hari\n"
        "⚡ Tidak perlu beli lagi besok"
    ),

    # 1H → 7H
    ("1hari", "7hari"): (
        "🔥 Pilihan paling banyak diambil\n\n"
        "💎 <b>VIP 7 Hari lebih worth it</b>\n"
        "📉 Jauh lebih hemat per hari\n"
        "🚀 Nonton lebih puas tanpa khawatir habis"
    ),

    # 3H → 7H
    ("3hari", "7hari"): (
        "💡 Sekalian yang lebih hemat\n\n"
        "💎 <b>VIP 7 Hari lebih untung</b>\n"
        "📉 Harga per hari lebih murah\n"
        "⚡ Tidak repot perpanjang cepat"
    ),

    # 7H → 10H
    ("7hari", "10hari"): (
        "🔥 Upgrade favorit pengguna\n\n"
        "💎 <b>VIP 10 Hari lebih lega</b>\n"
        "📉 Tambah sedikit, durasi lebih panjang\n"
        "🚀 Lebih nyaman untuk lanjut marathon"
    ),

    # 10H → 15H
    ("10hari", "15hari"): (
        "💡 Selisih sedikit lebih untung\n\n"
        "💎 <b>VIP 15 Hari lebih hemat</b>\n"
        "📉 Harga per hari makin murah\n"
        "⚡ Lebih nyaman tanpa sering top up"
    ),

    # 15H → 30H
    ("15hari", "30hari"): (
        "👑 <b>VIP 30 Hari Best Value</b>\n\n"
        "📉 Harga per hari paling murah\n"
        "🚀 Sekali aktif aman sebulan penuh\n"
        "🔥 Paket paling favorit pengguna VIP"
    ),
}