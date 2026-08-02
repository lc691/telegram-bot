from pyrogram.types import BotCommand


def get_drac1n_commands() -> list[BotCommand]:
    """
    Daftar command utama Dracin1 Bot (user-facing).
    """

    return [
        # =========================
        # BASIC COMMANDS
        # =========================
        BotCommand(
            "start",
            "🚀 Mulai / refresh bot"
        ),
        BotCommand(
            "status",
            "📊 Cek status akun kamu"
        ),

        # =========================
        # MONETIZATION
        # =========================
        BotCommand(
            "referral",
            "💰 Dapatkan komisi 20% dari referral"
        ),
        BotCommand(
            "redeem",
            "🎁 Redeem voucher / VIP code"
        ),

        # =========================
        # FEEDBACK
        # =========================
        BotCommand(
            "feedback",
            "📮 Kirim masukan, laporan, atau saran fitur"
        ),

    ]