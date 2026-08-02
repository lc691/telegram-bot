import random

NO_TEXT_RESPONSES = [
    # --- Serius / Neutral
    "❗ Tidak ada teks terdeteksi di gambar.",
    "🤖 OCR tidak menemukan tulisan apapun.",
    "👀 Sepertinya gambar ini memang tanpa teks.",
    "🧐 Sudah diperiksa, tapi tidak ada kata yang bisa dibaca.",
    "📷 Gambarnya jernih, tapi teksnya nihil.",
    # --- Lucu / Santai
    "😂 OCR nyerah... kayaknya ini gambar tanpa tulisan.",
    "😅 Aku coba baca, tapi malah bengong. Kosong.",
    "🙃 Kayaknya ini puzzle tanpa huruf, OCR bingung total.",
    "😶 Gambar ini sepi... nggak ada kata-kata sama sekali.",
    "🤔 Hmm... kalau ada tulisannya, mungkin cuma hantu OCR yang bisa lihat.",
    # --- Sarkas / Nyeleneh
    "🙄 Serius, kamu kasih aku gambar polos? 😏",
    "😑 Nihil. Kosong. Nada.",
    "🤣 Kalau ada teksnya, pasti lagi main petak umpet.",
    "🤡 OCR bilang: 'Bro, aku buta huruf di gambar ini.'",
    "👻 Tulisan ghaib terdeteksi... oh tunggu, ga ada juga.",
    # --- Sopan / Friendly
    "🙏 Maaf, aku tidak menemukan teks di gambar ini.",
    "✨ Sudah dicek, tapi sepertinya tidak ada tulisan.",
    "😇 Gambar ini indah, tapi tidak ada teks yang bisa dibaca.",
    "📭 Kotak kosong... teksnya belum hadir.",
    "🌸 Aku coba deteksi, tapi hasilnya nihil ya.",
]


def get_no_text_message():
    return random.choice(NO_TEXT_RESPONSES)
