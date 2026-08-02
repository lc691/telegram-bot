import random
import re
from html import escape

from config import SOURCE_CHANNEL_MAP

DOCTOR_HOOKS = [
    "💉 Mereka menghina tabib yang salah...",
    "🏥 Tak ada yang tahu dia dokter legendaris...",
    "😷 Saat semua orang putus asa, mereka baru mencarinya...",
]

RICH_HOOKS = [
    "💰 Mereka mengusir pewaris keluarga terkaya...",
    "👑 Wanita miskin itu ternyata konglomerat...",
]

REVENGE_HOOKS = [
    "🥀 Dibuang keluarganya, kini semua menyesal...",
    "🔥 Orang yang mereka hina akhirnya kembali...",
]

ROMANCE_HOOKS = [
    "💔 Dia baru sadar siapa pria yang dinikahinya...",
    "😭 Mantannya akhirnya menyesal...",
]

DEFAULT_HOOKS = [
    "👀 Rahasia besarnya akhirnya terbongkar...",
]

CTA_TITLES = [
    "💔 Lanjut Cerita yang Bikin Hancur",
    "🔥 Ending yang Tidak Terduga",
    "👀 Jangan Lewatkan Bagian Ini",
    "😱 Semua Terungkap di Sini",
    "📺 Lanjut ke Twist Berikutnya",
]

CTA_SUBTITLES = [
    "💎 Full episode tanpa iklan",
    "💎 Akses sebelum dihapus",
    "💎 Unlock cerita lengkap sekarang",
]

CLIFFHANGERS = [
    "💔 Ternyata orang yang ia percaya… adalah orang yang menghancurkannya...",
    "😱 Fakta yang disembunyikan akhirnya terungkap...",
    "💀 Tapi semuanya sudah terlambat untuk diperbaiki...",
    "👀 Dan pria itu tidak pernah benar-benar pergi...",
    "🔥 Apa yang terjadi setelah itu jauh lebih buruk...",
]

BAD_ENDINGS = {
    "dan", "yang", "karena", "untuk",
    "dengan", "adalah", "bahwa"
}

def generate_full_caption(
    title,
    sinopsis,
    genre,
    hashtags,
    files,
    bot_username,
    source_code,
    source_label,
    is_adult=False,
    compact=False,
):

    # =====================================================
    # UTIL
    # =====================================================
    def clean(text):
        return re.sub(r"[\uD800-\uDFFF]", "", text.strip()) if text else ""

    def clean_hashtags(tags: str, is_adult: bool):
        default = ["#dramachina", "#shortdrama"]
        if is_adult:
            default.append("#dewasa")

        extra = []
        if tags:
            parts = re.split(r"[,\n]", tags)
            for part in parts:
                tag = re.sub(r"[^a-z0-9]", "", part.strip().lower())
                if tag:
                    extra.append(f"#{tag}")

        unique = list(dict.fromkeys(default + extra))
        return " ".join(unique)

    def extract_range(file_name):
        match = re.search(r"(\d+)[\-_–](\d+)(END)?", file_name.upper())
        if match:
            start = int(match.group(1))
            end = int(match.group(2))
            is_end = bool(match.group(3))
            return start, end, is_end
        return 0, 0, False

    def generate_hook(title, sinopsis):
        text = f"{title} {sinopsis}".lower()

        if any(k in text for k in [
            "dokter", "tabib", "rumah sakit", "medis"
        ]):
            pool = DOCTOR_HOOKS

        elif any(k in text for k in [
            "miliarder", "konglomerat", "kaya", "pewaris"
        ]):
            pool = RICH_HOOKS

        elif any(k in text for k in [
            "mantan", "cerai", "suami", "istri"
        ]):
            pool = ROMANCE_HOOKS

        elif any(k in text for k in [
            "dibuang", "pengkhianatan", "balas dendam"
        ]):
            pool = REVENGE_HOOKS

        else:
            pool = DEFAULT_HOOKS

        return random.choice(pool)

    def generate_cta():
        cliffhanger = random.choice(CLIFFHANGERS)
        cta_title = random.choice(CTA_TITLES)
        cta_subtitle = random.choice(CTA_SUBTITLES)

        return cliffhanger, cta_title, cta_subtitle

    def shorten_sinopsis(text, limit=140):
        text = clean(text)

        if not text:
            return ""

        text = re.sub(r"\s+", " ", text).strip()

        if len(text) <= limit:
            return text

        shortened = text[:limit].rsplit(" ", 1)[0]

        last_word = shortened.split()[-1].lower()

        if last_word in BAD_ENDINGS:
            shortened = shortened.rsplit(" ", 1)[0]

        return shortened + "..."

    def build_source_block(code: str, label: str):
        key = code.lower().strip()
        channels = SOURCE_CHANNEL_MAP.get(key)

        # fallback kalau tidak ada mapping
        if not channels:
            return f"<b>{escape(label)}</b>\n", ""

        main_url = f"https://t.me/{channels[0]}"

        source_text = (
            f'<b>{escape(label)}</b> | <a href="{main_url}">📚 <b>LIST DRAMA</b></a>\n'
        )
        cta_text = ""

        return source_text, cta_text

    # =====================================================
    # CLEAN INPUT
    # =====================================================
    title = clean(title)

    genre = clean(genre)

    sinopsis = shorten_sinopsis(sinopsis)

    if sinopsis.lower() == "none":
        sinopsis = ""

    hashtags = clean(hashtags)

    if hashtags.lower() in ["none", "#none"]:
        hashtags = ""

    source_code = clean(source_code)
    source_label = clean(source_label)

    hashtags = clean_hashtags(hashtags, is_adult)

    hook = generate_hook(title, sinopsis)
    cliffhanger, cta_title, cta_subtitle = generate_cta()

    total_files = len(files)
    max_episode = 0

    # =====================================================
    # BUILD EPISODE LIST
    # =====================================================
    episode_lines = []
    source_text, source_cta = build_source_block(source_code, source_label)

    # Urutkan berdasarkan episode awal
    sorted_files = sorted(files, key=lambda f: extract_range(f[0])[0])

    for file_name, free_hash, paid_hash in sorted_files:
        file_name = clean(file_name)
        start, end, is_end = extract_range(file_name)
        if not start or not end:
            continue

        max_episode = max(max_episode, end)
        label = f"{start}–{end}{' END' if is_end else ''}"

        # ✅ Logika akses Gratis/VIP
        if start <= 10:
            is_free = True
        elif start <= 20 and total_files >= 4:
            is_free = True
        else:
            is_free = False

        text = "▶️ <b>Mulai Nonton</b> 👈 <i>Klik Disini</i>" if is_free else "🔐 <b>VIP Exclusive</b>"
        link_hash = free_hash if is_free else paid_hash
        link = f"https://t.me/{bot_username}?start={link_hash}"

        full_label = f"🎁 <b>Episode {label} • GRATIS</b>"
        episode_lines.append(f'{full_label}\n<a href="{link}">{text}</a>\n')

    # =====================================================
    # COMPACT LIMIT LOGIC (PHOTO MODE)
    # =====================================================
    MAX_FULL_BLOCK = 1
    MAX_COMPACT_BLOCK = 1

    total_blocks = len(episode_lines)

    if compact:
        visible_blocks = episode_lines[:MAX_COMPACT_BLOCK]

        if total_blocks > MAX_COMPACT_BLOCK:
            visible_blocks.append(
                "👀 <i>Lihat kelanjutannya di VIP</i>\n"
            )

    else:
        visible_blocks = episode_lines[:MAX_FULL_BLOCK]

        if total_blocks > MAX_FULL_BLOCK:
            visible_blocks.append(
                "😱 Tapi dia bukan orang yang mereka kira...\n"
                "💔 Semuanya sudah terlambat...\n"
            )

    # =====================================================
    # CAPTION SECTIONS
    # =====================================================
    sections = []

    # HOOK
    sections.append(f"{hook}\n")

    # HEADER
    header = (
        f"🎬 <b>{escape(title)}</b>\n"
        f"{source_text}{source_cta}\n"
        f"<b>{escape(genre)} | Subtitle Indonesia</b>\n"
    )

    if is_adult:
        header += "⚠️ <b>Konten 18+</b>\n"

    sections.append(header)

    # SINOPSIS (hanya kalau ada & bukan compact)
    if sinopsis and not compact:

        safe_sinopsis = (
            sinopsis
            .replace("\r", "")
            .strip()
        )

        safe_sinopsis = re.sub(
            r"\n{3,}",
            "\n\n",
            safe_sinopsis
        )

        sections.append(
            "📝 <b>SINOPSIS</b>\n"
            f"<i>{safe_sinopsis}</i>\n"
        )

    # EPISODE LIST
    sections.append(
        # "<b><u>🎬 TONTON SEKARANG</u></b>\n"
        "═══════✦✧✦═══════\n" + "\n".join(visible_blocks) + "═══════✦✧✦═══════\n"
    )

    # CTA / MARKETING
    if compact:
        sections.append(
            f'👀 <a href="https://t.me/{bot_username}?start=vip">'
            f'<b>Lihat Kelanjutannya</b></a>\n'
            f'{VIP_PRICE_TEXT}\n'
        )
    else:
        sections.append(
            f"{cliffhanger}\n\n"
            f'<a href="https://t.me/{bot_username}?start=vip">'
            f"<b>{cta_title}</b></a> 👈\n"
            f"<i>{cta_subtitle}</i>\n\n"

            f"📖 <b>PANDUAN & BANTUAN</b>\n"
            f'📚 <a href="https://t.me/tutorialvip1/22">'
            f"<b>Panduan VIP</b></a>\n"
            f"📞 <b>Admin:</b> @mimindcstv\n\n"
        )
    # HASHTAGS
    sections.append(escape(hashtags))

    # =====================================================
    # FINAL CAPTION
    # =====================================================
    return "\n".join(sections).strip()

