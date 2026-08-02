import re


def resolve_is_paid_from_filename(file_name: str) -> bool:
    """
    FINAL EPISODE POLICY (PRODUCTION)

    Rules:
    - Episode 1–20        → FREE
    - Episode >=21        → PAID
    - Mengandung 'END'    → PAID
    - Tidak ada angka     → PAID (fail-safe)

    Contoh:
    - "Judul 1-20.mp4"        → False
    - "Judul 21-40.mp4"       → True
    - "Judul 41-70END.mp4"    → True
    - "Judul Spesial.mp4"     → True
    """

    name = file_name.upper()

    # 1️⃣ END selalu PAID
    if "END" in name:
        return True

    # 2️⃣ Ambil angka episode pertama
    match = re.search(r"(\d+)", name)
    if not match:
        return True  # fail-safe

    episode = int(match.group(1))

    # 3️⃣ Boundary FINAL
    return episode >= 21
