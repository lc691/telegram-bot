def build_voucher_text(
    *,
    title: str,
    content: str,
    vouchers: list[str],
    amount: int,
    duration: int,
) -> str:
    voucher_lines = "\n".join(
        f"🔑 <spoiler>{v}</spoiler>\u200b" for v in vouchers
    )

    return (
        f"<b>{title}</b>\n\n"
        f"{content}\n\n"
        f"🎁 Ada <b>{amount}</b> voucher VIP "
        f"<b>{duration} hari</b>:\n\n"
        f"{voucher_lines}\n\n"
        "Gunakan <code>/redeem KODE</code> untuk klaim 🚀"
    )
