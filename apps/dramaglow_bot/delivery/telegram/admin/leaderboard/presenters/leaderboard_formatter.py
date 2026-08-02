from datetime import datetime
from zoneinfo import ZoneInfo
from ....user.common.konstanta import MAX_PAGE

WIB = ZoneInfo("Asia/Jakarta")


def format_vip_leaderboard(*, data, period, page, page_size, total_count, date=None):
    """
    Format text leaderboard VIP.
    - UI only (no I/O, no logging)
    - Date diasumsikan WIB
    """

    titles = {
        "daily": "🔥 <b>Top VIP Harian</b>",
        "weekly": "📆 <b>Top VIP Mingguan</b>",
        "monthly": "📅 <b>Top VIP Bulanan</b>",
        "all": "🏆 <b>Top VIP Sepanjang Masa</b>",
    }

    lines: list[str] = [titles.get(period, "🏆 <b>Top VIP</b>")]

    # ===============================
    # HEADER: DATE (DAILY ONLY)
    # ===============================
    if period == "daily" and date:
        try:
            # date = YYYY-MM-DD (WIB)
            d = datetime.strptime(date, "%Y-%m-%d")
            label = d.strftime("%d %B %Y")
            lines.append(f"📅 Tanggal: <b>{label}</b>")
        except ValueError:
            # fallback silent (UI tetap jalan)
            pass

    # ===============================
    # HEADER: TOTAL
    # ===============================
    lines.append(f"📊 Total pembelian: <b>{total_count}</b>")
    lines.append("")

    # ===============================
    # EMPTY STATE
    # ===============================
    if not data:
        lines.append(
            "<i>Belum ada transaksi VIP pada tanggal ini.</i>"
            if period == "daily"
            else "<i>Belum ada transaksi VIP pada periode ini.</i>"
        )
        return "\n".join(lines)

    # ===============================
    # LIST ITEMS
    # ===============================
    start = (page - 1) * page_size + 1

    for i, row in enumerate(data):
        rank = start + i
        username = row.get("username") or "-"
        total_purchase = row.get("total_purchase", 0)

        lines.append(f"{rank:02d}. {username} — <b>{total_purchase}x</b> VIP")

    # ===============================
    # FOOTER: PAGE
    # ===============================
    lines.append("")
    lines.append(f"📄 Halaman {min(page, MAX_PAGE)}/{MAX_PAGE}")

    return "\n".join(lines)
