import random

# --- Pesan untuk Paid Hash (VIP only) ---
PAID_MESSAGES = [
    "💎 <b>Konten ini eksklusif hanya untuk VIP.</b>\n<b>Upgrade sekarang untuk membuka ceritanya!</b>\n\n<b>— Drama China Short TV 🎬</b>",
    "🚀 <b>Mau lanjut ke bab berikutnya?</b>\n<b>Hanya VIP yang bisa masuk ✨</b>\n\n<b>— Drama China Short TV 🎬</b>",
    "🔒 <b>Episode terkunci.</b>\n<b>Kuncinya cuma satu: VIP Card 💎</b>\n\n<b>— Drama China Short TV 🎬</b>",
    "👑 <b>Yang spesial hanya untuk yang spesial.</b>\n<b>Upgrade ke VIP sekarang!</b>\n\n<b>— Drama China Short TV 🎬</b>",
    "🤣 <b>Gratisan minggir dulu…</b>\n<b>VIP aja yang boleh lewat sini.</b>\n\n<b>— Drama China Short TV 🎬</b>",
    "🎬 <b>Adegan spesial ini cuma tayang buat VIP ✨</b>\n\n<b>— Drama China Short TV 🎬</b>",
    "🔥 <b>VIP itu kayak karakter utama.</b>\n<b>Gratisan cuma figuran 😎</b>\n\n<b>— Drama China Short TV 🎬</b>",
    "🚫 <b>Akses ditolak.</b>\n<b>VIP selalu diterima 💎</b>\n\n<b>— Drama China Short TV 🎬</b>",
    "🎉 <b>Semua ending manis hanya untuk VIP!</b>\n\n<b>— Drama China Short TV 🎬</b>",
    "✨ <b>Mau full drama experience?</b>\n<b>VIP jawabannya.</b>\n\n<b>— Drama China Short TV 🎬</b>",
    "📺 <b>Adegan premium ini nggak ada di versi gratis.</b>\n\n<b>— Drama China Short TV 🎬</b>",
    "💔 <b>Gratis berhenti di opening.</b>\n<b>VIP sampai ending!</b>\n\n<b>— Drama China Short TV 🎬</b>",
    "😏 <b>Rahasia cerita ini cuma buat VIP.</b>\n<b>Upgrade biar tau kelanjutannya!</b>\n\n<b>— Drama China Short TV 🎬</b>",
    "🤣 <b>VIP itu kayak punya remote kontrol,</b>\n<b>gratisan cuma bisa nonton iklan.</b>\n\n<b>— Drama China Short TV 🎬</b>",
    "🌟 <b>Lanjut cerita eksklusif hanya untuk VIP Club.</b>\n\n<b>— Drama China Short TV 🎬</b>",
]


# --- Pesan untuk Free Hash (kuota gratis habis) ---
FREE_MESSAGES = [
    "⚠️ <b>Kuota gratismu sudah habis.</b>\n\n💎 <b>Upgrade VIP untuk lanjut nonton tanpa batas!</b>\n\n<b>— Drama China Short TV 🎬</b>",
    "😢 <b>Episode berhenti di sini…</b>\n<b>Mau lanjut? Jadilah VIP sekarang!</b>\n\n<b>— Drama China Short TV 🎬</b>",
    "🚪 <b>Akses gratis sudah ditutup.</b>\n<b>VIP selalu punya pintu terbuka ✨</b>\n\n<b>— Drama China Short TV 🎬</b>",
    "🎬 <b>Gratisan tamat di sini.</b>\n<b>VIP = full season unlocked 💎</b>\n\n<b>— Drama China Short TV 🎬</b>",
    "😂 <b>Drama gratis habis.</b>\n<b>Jangan sedih, upgrade VIP biar bisa maraton!</b>\n\n<b>— Drama China Short TV 🎬</b>",
    "🔥 <b>Gratisan cuma opening.</b>\n<b>VIP yang punya full season!</b>\n\n<b>— Drama China Short TV 🎬</b>",
    "⏳ <b>Ceritamu berhenti di tengah jalan…</b>\n<b>Lanjutkan dengan jadi VIP.</b>\n\n<b>— Drama China Short TV 🎬</b>",
    "🤔 <b>Kok berhenti?</b>\n<b>Karena gratisan udah limit. VIP nggak kenal limit 😎</b>\n\n<b>— Drama China Short TV 🎬</b>",
    "📺 <b>Eps gratis = tamat.</b>\n<b>VIP = semua episode unlocked 💎</b>\n\n<b>— Drama China Short TV 🎬</b>",
    "🚫 <b>Akses gratis habis.</b>\n<b>VIP nggak pernah habis.</b>\n\n<b>— Drama China Short TV 🎬</b>",
    "💔 <b>Drama gratis berhenti di sini.</b>\n<b>Happy ending hanya untuk VIP ✨</b>\n\n<b>— Drama China Short TV 🎬</b>",
    "😂 <b>Gratis = filler arc.</b>\n<b>VIP = main story yang asli.</b>\n\n<b>— Drama China Short TV 🎬</b>",
    "🎉 <b>Udah panas-panas malah stop?</b>\n<b>VIP lanjut terus sampe ending!</b>\n\n<b>— Drama China Short TV 🎬</b>",
    "🔒 <b>Eps ini terkunci.</b>\n<b>VIP selalu punya kuncinya 💎</b>\n\n<b>— Drama China Short TV 🎬</b>",
    "🙃 <b>Mau ending?</b>\n<b>Ya jadi VIP dulu lah…</b>\n\n<b>— Drama China Short TV 🎬</b>",
]


def get_random_free_message():
    return random.choice(FREE_MESSAGES)


def get_random_paid_message():
    return random.choice(PAID_MESSAGES)
