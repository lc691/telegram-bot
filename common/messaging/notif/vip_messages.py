import html
import re

from common.messaging.notif.time_utils import format_wib


def build_vip_message(
    username: str,
    paket: str,
    mention: str,
    mode: str,
    via_voucher: bool,
    basic_days: int,
    bonus_days: int,
    old_vip_end,
    new_vip_end,
    purchases: int = 1,
) -> str:
    """
    Build VIP announcement message.
    Pure presenter only.
    """

    # =====================================================
    # SAFE DATA
    # =====================================================

    paket_safe = html.escape(paket)

    old_vip_end_str = (
        format_wib(old_vip_end)
        if old_vip_end
        else None
    )

    new_vip_end_str = format_wib(new_vip_end)

    purchases = max(1, purchases)

    # =====================================================
    # DURATION INFO
    # =====================================================

    total_days = basic_days + bonus_days

    durasi_text = f"<b>{basic_days} hari</b>"

    bonus_text = (
        f" (+{bonus_days} hari 🎁)"
        if bonus_days > 0
        else ""
    )

    total_text = f"<b>{total_days} hari</b>"

    # =====================================================
    # HEADER
    # =====================================================

    if via_voucher:

        header = (
            "🎁 <b>VOUCHER VIP BERHASIL DIREDEEM!</b>"
        )

        hashtags = "#VoucherVIP #PremiumAccess"

    else:

        if mode == "baru":

            header = (
                "💎 <b> VIP AKTIF — PREMIUM ACCESS</b>"
            )

            hashtags = "#VIP #New #PremiumAccess"

        else:

            header = (
                "♻️ <b>VIP BERHASIL DIPERPANJANG</b>"
            )

            hashtags = "#VIP #Extend #StayPremium"

    # =====================================================
    # DETAIL BLOCK
    # =====================================================

    detail_block = (
        f"📊 <b>Durasi:</b> {durasi_text}{bonus_text}\n"
        f"➕ <b>Total Benefit:</b> {total_text}"
    )

    # =====================================================
    # VIP BENEFITS
    # =====================================================

    if mode == "baru":

        vip_value = (
            "\n👑 <b>Benefit VIP Aktif:</b>\n"
            "├─ Streaming bebas iklan\n"
            "├─ Akses lebih cepat\n"
            "├─ Konten premium eksklusif\n"
            "└─ Prioritas member VIP"
        )

    else:

        vip_value = (
            "\n👑 <b>Akses VIP tetap aktif.</b>"
        )

    # =====================================================
    # PACKAGE TAG
    # =====================================================

    paket_tag = re.sub(
        r"[^0-9A-Za-z]",
        "",
        paket_safe,
    )

    if paket_tag:
        hashtags += f" #VIP_{paket_tag}"

    # =====================================================
    # OPTIONAL OLD VIP INFO
    # =====================================================

    old_block = ""

    if old_vip_end_str and mode == "extend":

        old_block = (
            f"\n⏳ <b>VIP Sebelumnya:</b>\n"
            f"<code>{old_vip_end_str}</code>\n"
        )

    # =====================================================
    # FINAL MESSAGE
    # =====================================================

    msg = f"""
{header}

👤 <b>User:</b> {mention}
📦 <b>Paket:</b> <code>{paket_safe}</code>
⭐ <b>Pembelian ke:</b> {purchases}

═══════✦✧✦═══════
{detail_block}
{old_block}
📆 <b>Aktif Sampai:</b>
<code>{new_vip_end_str}</code>
{vip_value}
═══════✦✧✦═══════

{hashtags}
""".strip()

    return re.sub(r"\n{3,}", "\n\n", msg)