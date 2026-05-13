import html
import re

from common.messaging.notif.time_utils import format_wib


def build_vip_message(
    username: str,
    paket: str,
    mention: str,
    mode: str,  # "baru" | "extend"
    via_voucher: bool,
    basic_days: int,
    bonus_days: int,
    old_vip_end,
    new_vip_end,
) -> str:
    """
    Bangun pesan pengumuman VIP.
    PURE presenter (tanpa logic bisnis).
    """
    paket_safe = html.escape(paket)

    # --- Format waktu ke WIB ---
    old_vip_end_str = format_wib(old_vip_end) if old_vip_end else "–"
    new_vip_end_str = format_wib(new_vip_end)

    # --- Durasi paket ---
    durasi_text = f"<b>{basic_days} hari</b>"
    bonus_text = f" (+{bonus_days} hari 🎁)" if bonus_days > 0 else ""
    total_text = f"<b>{basic_days + bonus_days} hari</b>"

    # --- Header & pesan ---
    if via_voucher:
        header = "🎉🎁 <b>VOUCHER VIP SUKSES DIREDEEM!</b> 🎁🎉"
        if mode == "baru":
            extra_line = f"📅 Durasi Voucher:\n   └─ {durasi_text}"
        else:
            extra_line = (
                f"📅 Tambahan Voucher:\n   └─ {durasi_text}{bonus_text}\n\n"
                f"📆 Total Ditambahkan:\n   └─ {total_text}"
            )
        hashtags = "#VoucherVIP #Redeem" + (" #Extend" if mode == "extend" else "")
    else:
        if mode == "baru":
            header = "🎉 <b>SELAMAT! VIP Telah Aktif</b> 🎉"
            extra_line = (
                f"📅 Durasi Awal:\n   └─ {durasi_text}{bonus_text}\n\n"
                f"📆 Total Aktif:\n   └─ {total_text}"
            )
            hashtags = "#VIP #Baru #Streaming"
        else:
            header = "🎉 <b>VIP Berhasil Diperpanjang</b> 🎉"
            extra_line = (
                f"📅 Durasi Tambahan:\n   └─ {durasi_text}{bonus_text}\n\n"
                f"📆 Total Ditambahkan:\n   └─ {total_text}"
            )
            hashtags = "#VIP #Extend #Streaming"

    # --- Footer keistimewaan (VIP baru non-voucher) ---
    vip_footer = ""
    if not via_voucher and mode == "baru":
        vip_footer = (
            "\n🚀 <b>Keistimewaan VIP:</b>\n"
            "✅ Streaming bebas iklan\n"
            "✅ Akses episode lebih awal\n"
            "✅ Konten premium eksklusif\n"
            "✅ Grup diskusi VIP"
        )

    # --- Hashtag paket --- 
    paket_tag = re.sub(r"[^0-9A-Za-z]", "", paket_safe)
    if paket_tag:
        hashtags += f" #VIP_{paket_tag}"

    # --- Build pesan final ---
    msg = f"""
{header}
━━━━━━━━━━━━━━━━━━━━━━━
👑 Pengguna: {mention}
📦 Paket : <code>{paket_safe}</code>

⏳ VIP Sebelumnya:
   └─ <code>{old_vip_end_str}</code>

{extra_line}

📆 VIP Aktif Hingga:
   └─ <code>{new_vip_end_str}</code>
{vip_footer}
━━━━━━━━━━━━━━━━━━━━━━━
{hashtags}
""".strip()

    # Hapus newline berlebih
    return msg.replace("\n\n\n", "\n\n")
