import re
import unicodedata

# ================================
# === Escape Markdown (v1/v2) ===
# ================================

# Untuk Telegram Markdown v1 (ParseMode.MARKDOWN)
ESCAPE_CHARS_MD1 = r"_*[]()`!."


def escape_md(text: str) -> str:
    """
    Escape karakter khusus Markdown v1 agar tidak rusak format.
    """
    if not isinstance(text, str):
        text = str(text)
    return re.sub(f"([{re.escape(ESCAPE_CHARS_MD1)}])", r"\\\1", text)


# Untuk Telegram Markdown v2 (ParseMode.MARKDOWN_V2)
ESCAPE_CHARS_MD2 = r"_*[]()~`>#+-=|{}.!\\"


def escape_md_v2(text: str) -> str:
    """
    Escape semua karakter khusus yang diperlukan oleh Telegram Markdown v2.
    """
    if not isinstance(text, str):
        text = str(text)
    return re.sub(f"([{re.escape(ESCAPE_CHARS_MD2)}])", r"\\\1", text)


# ========================
# === Slug Generator  ====
# ========================


def slugify(text: str) -> str:
    """
    Buat slug URL-friendly dari judul atau teks.
    Contoh: "Drama Indonesia 2023!" -> "drama-indonesia-2023"
    """
    if not text:
        text = ""
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^\w]+", "-", text.strip().lower()).strip("-")
    return slug or "untitled"


# ===========================
# === File Name Beautify ====
# ===========================


def beautify_file_name(file_name: str) -> str:
    """
    Bersihkan dan rapikan nama file jadi bentuk yang bisa dibaca manusia.
    Contoh: "balas_dendam-ep1-10.mp4" -> "Balas Dendam"
    """
    if not file_name:
        return "Tanpa Judul"

    name = file_name

    # 1. Hapus ekstensi
    name = re.sub(r"\.[a-zA-Z0-9]{2,4}$", "", name)

    # 2. Ganti separator jadi spasi
    name = re.sub(r"[\._\-]", " ", name)

    # 3. Hapus episode/angka di akhir
    name = re.sub(r"\s*\d+(-\d+)?(END)?$", "", name, flags=re.IGNORECASE)

    # 4. Hapus kode episode seperti ep01, s01e02
    name = re.sub(r"(s\d+e\d+|ep\d+)", "", name, flags=re.IGNORECASE)

    # 5. Capitalize setiap kata
    name = " ".join(w.capitalize() for w in name.split())

    return name.strip()


# ====================
# === Format Ukuran ==
# ====================


def format_size(size_bytes: int) -> str:
    """
    Format ukuran file dari byte ke KB / MB / GB secara human-readable.
    """
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.2f}{unit}"
        size_bytes /= 1024
    return f"{size_bytes:.2f}PB"
