def get_user_table(source: str) -> str:
    """Kembalikan nama tabel user berdasarkan sumber bot"""
    if source == "utbk":
        return "users_utbk"
    return "users"  # default: drac1n


def get_source_bot(source: str) -> str:
    """Kembalikan nilai untuk kolom 'source_bot' (bukan nama tabel)"""
    return source if source in {"drac1n", "utbk"} else "drac1n"


def get_vip_logs_table() -> str:
    """Nama tabel log VIP (bersama semua bot)"""
    return "vip_logs"


def get_donation_table() -> str:
    """Nama tabel donasi (bersama semua bot)"""
    return "donation_log"
