import random
from typing import Optional

BOT_MOODS: dict[str, list[str]] = {

    # =========================
    # 😔 SEDIH / GAGAL HALUS
    # =========================
    "sedih": [
        "😔 Belum ketemu hasilnya…",
        "🥀 Masih kosong, dramanya belum muncul",
        "💔 Yah… belum ada yang cocok",
        "😢 Dramanya belum ditemukan",
        "🫠 Nihil hasil, semoga nanti ada ya",
    ],

    # =========================
    # 😂 LUCU / RINGAN
    # =========================
    "lucu": [
        "🤣 Hasilnya kabur duluan",
        "🫣 Dramanya lagi ngumpet",
        "😆 Belum ketemu, mungkin lagi liburan",
        "👻 Dramanya ghosting kita",
        "😴 Kayaknya dramanya lagi tidur",
    ],

    # =========================
    # 🙂 NETRAL RAMAH
    # =========================
    "netral": [
        "🙂 Belum ada hasil, coba lagi ya",
        "🔍 Data belum ditemukan",
        "📭 Masih kosong, silakan cari judul lain",
        "📝 Belum ada data yang cocok",
    ],

    # =========================
    # 🤖 BOT PERSONA
    # =========================
    "bot": [
        "🤖 Aku sudah cari-cari, tapi belum ketemu",
        "🧠 Mesin pencari belum nemu hasil",
        "⚙️ Query diterima, hasil masih kosong",
        "📡 Data belum berhasil ditangkap",
    ],

    # =========================
    # 🎭 DRAMATIS (BIAR HIDUP)
    # =========================
    "dramatis": [
        "🎭 Sunyi… tak ada hasil yang muncul",
        "🌫️ Pencarian berakhir tanpa jejak",
        "🕯️ Hening… dramanya belum terlihat",
        "🖤 Tidak satu pun hasil menampakkan diri",
    ],
}


def get_bot_mood(mood: Optional[str] = None) -> str:
    """
    Ambil satu kalimat mood bot (FULL EMOJI).
    - Mood valid → ambil dari kategori
    - Mood None / invalid → acak lintas kategori
    """

    if mood and mood in BOT_MOODS:
        return random.choice(BOT_MOODS[mood])

    return random.choice(
        random.choice(list(BOT_MOODS.values()))
    )
