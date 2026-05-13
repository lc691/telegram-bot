from config import SOURCE_CHANNEL_MAP


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
    import re
    from html import escape

    # =====================================================
    # UTIL
    # =====================================================
    def clean(text):
        return re.sub(r"[\uD800-\uDFFF]", "", text.strip()) if text else ""

    def clean_hashtags(tags: str, is_adult: bool):
        default = ["#dracinshort", "#dramashort", "#dramaglow", "#dramachina"]
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
    sinopsis = clean(sinopsis)
    source_code = clean(source_code)
    source_label = clean(source_label)
    hashtags = clean_hashtags(hashtags, is_adult)

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

        text = "🆓 Free Access" if is_free else "🔐 VIP Exclusive"
        link_hash = free_hash if is_free else paid_hash
        link = f"https://t.me/{bot_username}?start={link_hash}"

        full_label = f"<b>Episode {label}</b>"
        episode_lines.append(f'{full_label}\n<a href="{link}">{text}</a>\n')

    # =====================================================
    # COMPACT LIMIT LOGIC (PHOTO MODE)
    # =====================================================
    MAX_PHOTO_BLOCK = 3
    total_blocks = len(episode_lines)

    if compact:
        if total_blocks > MAX_PHOTO_BLOCK:
            visible_blocks = episode_lines[:MAX_PHOTO_BLOCK]
            visible_blocks.append("\n🔽 <i>Episode lainnya tersedia di bot</i>\n")
        else:
            visible_blocks = episode_lines
    else:
        visible_blocks = episode_lines

    # =====================================================
    # CAPTION SECTIONS
    # =====================================================
    sections = []

    # HEADER
    header = (
        f"🎬 <b>{escape(title)}</b>\n"
        "💵 <b>Rp2.300 NONTON SEMUA DRAMA SEHARIAN</b>\n"
        f"{source_text}{source_cta}\n"
        f"<b>{escape(genre)} | Subtitle Indonesia</b>\n"
    )

    if is_adult:
        header += "⚠️ <b>Konten 18+</b>\n"

    sections.append(header)

    # SINOPSIS (hanya kalau ada & bukan compact)
    if sinopsis and not compact:
        sections.append("<b>📝 SINOPSIS</b>\n" f"{escape(sinopsis)}\n")

    # EPISODE LIST
    sections.append(
        "<b><u>📜 LINK EPISODE 📜</u></b>\n"
        "═══════✦✧✦═══════\n" + "\n".join(visible_blocks) + "═══════✦✧✦═══════\n"
    )

    # CTA / MARKETING
    if compact:
        sections.append(
            "\n<b>💠 VIP:</b> "
            '<a href="https://t.me/drac1n_bot?start=vip">Akses</a> | '
            '<a href="https://t.me/drac1n_bot?start=referral">Partner</a>\n'
        )
    else:
        sections.append(
            "<b>💰 Mau cuan cuma modal rebahan?</b>\n"
            '<a href="https://t.me/drac1n_bot?start=referral">'
            "Gabung jadi partner promosi</a>\n\n"
            "<b>💠 AKSES VIP - TONTON BEBAS</b>\n"
            '<a href="https://t.me/drac1n_bot?start=vip">Klik Disini</a>\n\n'
            "<b>🌐 VIP Manual:</b>\n"
            '<a href="https://t.me/c/2856310074/3">Indonesia</a> | '
            '<a href="https://t.me/c/3871945880/3">Malaysia</a>\n\n'
            "<b>📖 PANDUAN & BANTUAN</b>\n"
            '📚 <a href="https://t.me/tutorialvip1/22">Panduan VIP</a>\n'
            "📞 Admin: @mimindcstv | @admischelia\n\n"
            "<b>⚠️ UNTUK YANG MAU REQUES DRAMA SILAHKAN KLIK DI BAWAH INI</b>\n"
            '🚀 <a href="https://t.me/dcstvgrup">DCSTV GRUP</a>\n'
        )

    # HASHTAGS
    sections.append(escape(hashtags))

    # =====================================================
    # FINAL CAPTION
    # =====================================================
    return "\n".join(sections).strip()
