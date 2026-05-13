# =====================[ UTIL DONASI ]=====================
import random


def normalize_donation_message(message: str | None) -> tuple[str, str]:
    """
    Normalisasi pesan donasi reguler.
    - Jika pesan kosong -> generate pesan random sesuai 'mood bot'
    - Tambahkan catatan (note) yang SELALU ada untuk donasi reguler
    - Return tuple (pesan_final, note_html)
    """
    panduan_note = "🚫 Pesan asli kosong — Lihat <a href='https://t.me/tutorialvip1'>Panduan VIP</a>"

    if message and message.strip():
        final_message = message.strip()
        return final_message, panduan_note

    fallback_messages = [
        "Donasi penuh keikhlasan 💖",
        "Support tanpa kata-kata 🙏",
        "Diam-diam tapi berarti 😎",
        "Donasi sunyi, berkah abadi ✨",
        "Tanpa pesan, tapi penuh makna 🌸",
    ]
    auto_msg = random.choice(fallback_messages)
    return auto_msg, panduan_note
