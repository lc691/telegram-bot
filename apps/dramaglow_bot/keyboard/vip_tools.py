from typing import Optional

from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from configs.logging_setup import log


def generate_vip_menus_markup() -> InlineKeyboardMarkup:
    """
    Generate menu pemilihan bot VIP (Glow / Drac1n / UTBK).
    """
    try:
        keyboard = [
            [
                InlineKeyboardButton("🧠 Glow", callback_data="vip_tools:glow"),
                InlineKeyboardButton("🧠 Drac1n", callback_data="vip_tools:drac1n"),
                InlineKeyboardButton("📘 UTBK", callback_data="vip_tools:utbk"),
            ],
            [InlineKeyboardButton("↩️ Kembali ke Dashboard", callback_data="dashboard")],
        ]
        return InlineKeyboardMarkup(keyboard)
    except Exception as e:
        log.error("[VIP_UI] Gagal generate VIP menu utama: %s", e, exc_info=True)
        return InlineKeyboardMarkup([])


def generate_vip_tools_markup(source: str = "") -> InlineKeyboardMarkup:
    """
    Generate markup untuk submenu VIP Tools berdasarkan bot sumber.

    Args:
        source (str): 'glow', 'drac1n', 'utbk', atau '' (default)

    Returns:
        InlineKeyboardMarkup: markup tombol
    """
    try:
        if source not in ("glow", "drac1n", "utbk", ""):
            log.warning(f"[VIP_UI] Unknown source: {source}")
            source = ""

        # Judul tombol statistik
        stat_title = {
            "glow": "📊 Statistik VIP (Glow)",
            "drac1n": "📊 Statistik VIP (Drac1n)",
            "utbk": "📊 Statistik VIP (UTBK)",
            "": "📊 Statistik VIP",
        }.get(source, "📊 Statistik VIP")

        keyboard = [
            [
                InlineKeyboardButton(
                    stat_title, callback_data=f"vip_stats:{source}:vip:0"
                ),
                InlineKeyboardButton("➕ Tambah VIP", callback_data="vip_add_start"),
            ],
            [
                InlineKeyboardButton(
                    "🔁 Perpanjang VIP", callback_data="vip_extend_start"
                ),
                InlineKeyboardButton("❌ Hapus VIP", callback_data="vip_delete_start"),
            ],
            [InlineKeyboardButton("♻️ Reset VIP", callback_data="vip_reset_menu")],
            [InlineKeyboardButton("⬅️ Kembali", callback_data="vip_tools_menu")],
        ]
        return InlineKeyboardMarkup(keyboard)

    except Exception as e:
        log.error("[VIP_UI] Gagal generate VIP tools markup: %s", e, exc_info=True)
        return InlineKeyboardMarkup([])


def generate_vip_reset_menu() -> InlineKeyboardMarkup:
    """
    Generate submenu untuk opsi reset VIP.
    """
    try:
        keyboard = [
            [
                InlineKeyboardButton(
                    "♻️ Reset Semua VIP", callback_data="vip_reset_all_confirm"
                )
            ],
            [
                InlineKeyboardButton(
                    "🆔 Reset by User ID", callback_data="vip_reset_start"
                )
            ],
            [InlineKeyboardButton("⬅️ Kembali", callback_data="vip_tools_menu")],
        ]
        return InlineKeyboardMarkup(keyboard)
    except Exception as e:
        log.error("[VIP_UI] Gagal generate VIP reset menu: %s", e, exc_info=True)
        return InlineKeyboardMarkup([])


def generate_reset_vip_confirm_buttons(
    all_reset: bool = True, user_id: Optional[int] = None
) -> InlineKeyboardMarkup:
    """
    Generate tombol konfirmasi untuk reset VIP.

    Args:
        all_reset (bool): True untuk reset semua user, False untuk 1 user saja
        user_id (int): user_id jika reset spesifik

    Returns:
        InlineKeyboardMarkup
    """
    try:
        if all_reset:
            yes_callback = "vip_reset_confirm_yes_all"
        elif user_id is not None:
            yes_callback = f"vip_reset_confirm_yes_id:{user_id}"
        else:
            log.warning("[VIP_UI] user_id tidak diberikan untuk reset spesifik.")
            return InlineKeyboardMarkup([])

        keyboard = [
            [
                InlineKeyboardButton("✅ Ya, lanjutkan", callback_data=yes_callback),
                InlineKeyboardButton("❌ Batal", callback_data="vip_tools_menu"),
            ]
        ]
        return InlineKeyboardMarkup(keyboard)

    except Exception as e:
        log.error(
            "[VIP_UI] Gagal generate tombol konfirmasi reset VIP: %s", e, exc_info=True
        )
        return InlineKeyboardMarkup([])


def generate_vip_package_buttons(mode: str = "vip_add") -> InlineKeyboardMarkup:
    """
    Generate package selection buttons for VIP add/extend.

    Args:
        mode (str): vip_add | vip_extend

    Returns:
        InlineKeyboardMarkup
    """
    try:
        prefix = "vip_add" if mode not in ("vip_add", "vip_extend") else mode

        keyboard = [
            [
                InlineKeyboardButton("1 Hari", callback_data=f"{prefix}_1hari"),
                InlineKeyboardButton("3 Hari", callback_data=f"{prefix}_3hari"),
            ],
            [
                InlineKeyboardButton("7 Hari", callback_data=f"{prefix}_7hari"),
                InlineKeyboardButton("15 Hari", callback_data=f"{prefix}_15hari"),
            ],
            [
                InlineKeyboardButton("30 Hari", callback_data=f"{prefix}_30hari"),
            ],
            [
                InlineKeyboardButton("Permanen", callback_data=f"{prefix}_permanen"),
            ],
            [InlineKeyboardButton("❌ Batal", callback_data=f"{prefix}_confirm_no")],
        ]
        return InlineKeyboardMarkup(keyboard)
    except Exception as e:
        log.error(f"Error generating VIP package buttons: {e}", exc_info=True)
        return InlineKeyboardMarkup([])


def generate_confirm_buttons(mode: str = "vip_add") -> InlineKeyboardMarkup:
    prefix = mode if mode in ("vip_add", "vip_extend") else "vip_add"
    buttons = [
        [
            InlineKeyboardButton("✅ Ya", callback_data=f"{prefix}_confirm_yes"),
            InlineKeyboardButton("❌ Tidak", callback_data=f"{prefix}_confirm_no"),
        ]
    ]
    return InlineKeyboardMarkup(buttons)


def generate_delete_confirm_buttons() -> InlineKeyboardMarkup:
    """
    Generate confirm/cancel buttons for deleting a VIP user.
    """
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "✅ Ya, hapus", callback_data="vip_delete_confirm_yes"
                )
            ],
            [InlineKeyboardButton("❌ Batal", callback_data="vip_delete_confirm_no")],
        ]
    )


def generate_vip_reset_confirm_buttons() -> InlineKeyboardMarkup:
    """
    Generate confirm/cancel buttons for resetting all VIP.
    """
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "✅ Ya, reset semua", callback_data="vip_reset_confirm_all"
                ),
                InlineKeyboardButton("❌ Batal", callback_data="vip_reset_cancel"),
            ]
        ]
    )
