import random

MODES = {
    "friendly": [
        "😄 Belum nemu yang mirip, coba kirim gambar lain ya!",
        "🙂 Aku belum menemukan yang cocok, coba poster lain deh.",
        "👋 Hmm, belum ketemu. Coba kirim yang lain!",
        "😊 Sepertinya belum ada yang cocok. Kirim ulang yuk!",
        "😇 Belum match nih, coba gambar lain ya!",
    ],
    "playful": [
        "😜 Hehe, AI-ku bingung liat ini. Coba kirim yang lain!",
        "😅 Aku nggak nemu yang cocok. Mau coba lagi?",
        "🎲 Tebak-tebakan gagal! Coba kirim ulang aja.",
        "✨ Poster keren, tapi belum ke-detect nih.",
        "🤭 Oops, belum nemu! Kirim yang lain yuk.",
    ],
    "formal": [
        "ℹ️ Tidak ditemukan hasil yang cukup mirip.",
        "🤖 Analisis selesai, tapi belum ada kecocokan.",
        "📄 Gambar tidak sesuai dengan data yang tersedia.",
        "🔎 Tidak ada hasil relevan. Coba gambar lain.",
        "📌 Hasil pencarian kosong, silakan kirim ulang.",
    ],
    "sad": [
        "😔 Belum ketemu yang cocok, maaf ya.",
        "🥺 Aku belum bisa menemukan yang mirip.",
        "💧 Hasilnya kosong. Coba kirim lagi ya?",
        "😞 Gagal nemu match, kirim ulang dong.",
        "😢 Aku juga sedih, belum ada yang pas.",
    ],
    "sassy": [
        "😤 Hm, ini kayaknya langka banget.",
        "🙃 Gambar unik, tapi belum nyambung di databasenya.",
        "🤨 Aku udah cari, tapi nggak ada yang mirip.",
        "😼 Coba lagi deh, mungkin aku lagi lemot.",
        "🔥 Gambar keren, tapi belum ketemu hasilnya.",
    ],
}


def get_no_match_message(mode: str | None = None) -> str:
    """Ambil pesan random dari mode tertentu (atau random mode)."""
    mode = mode if mode in MODES else random.choice(list(MODES))
    return random.choice(MODES[mode])
