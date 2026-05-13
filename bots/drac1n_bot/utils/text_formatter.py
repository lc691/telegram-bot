import os
import re


def format_filename(name: str) -> str:
    """
    Membersihkan nama file agar lebih rapi dan mudah dibaca.
    Contoh: "my_file.name.mp4" -> "My File Name"
    """
    name = os.path.splitext(name)[0]  # Hilangkan ekstensi
    name = re.sub(r"[_\.]+", " ", name)  # Ganti underscore/dot dengan spasi
    return name.title()  # Kapital tiap kata


def format_rupiah(amount: int) -> str:
    try:
        return f"Rp {amount:,}".replace(",", ".")
    except (ValueError, TypeError):
        return "Rp 0"
