# utils/chart_renderer.py
from io import BytesIO
from typing import List, Tuple


def render_donation_chart(
    data: List[Tuple],
    title: str = "Grafik Donasi VIP",
):
    # ⬇️ LAZY IMPORT (HANYA SAAT DIPANGGIL)
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        raise RuntimeError("Fitur grafik belum tersedia (matplotlib belum terpasang)")

    dates = [row[0].strftime("%d %b") for row in data]
    values = [row[1] for row in data]

    plt.figure(figsize=(8, 4))
    plt.plot(
        dates,
        values,
        marker="o",
        linestyle="-",
        linewidth=2,
    )
    plt.title(title)
    plt.xlabel("Tanggal")
    plt.ylabel("Jumlah (Rp)")
    plt.xticks(rotation=30)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()

    buf = BytesIO()
    plt.savefig(buf, format="png", dpi=120)
    buf.seek(0)

    plt.close("all")
    return buf
