from io import BytesIO

import matplotlib.pyplot as plt


def generate_donation_chart(data, title="Grafik Donasi VIP"):
    dates = [row[0].strftime("%d %b") for row in data]
    values = [row[1] for row in data]

    plt.figure(figsize=(8, 4))
    plt.plot(dates, values, marker="o", linestyle="-", color="blue", linewidth=2)
    plt.title(title)
    plt.xlabel("Tanggal")
    plt.ylabel("Jumlah (Rp)")
    plt.grid(True)
    plt.tight_layout()

    buf = BytesIO()
    plt.savefig(buf, format="png")
    buf.seek(0)
    plt.close()
    return buf
