from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

# HANYA label yang boleh memaksa urutan
PRIORITY_MAP = {
    "best value": 0,
    "hemat": 1,
}


def _package_priority(p: dict) -> tuple:
    """
    Urutan sorting:
    1. Priority label (Best Value, Hemat)
    2. Total hari (desc)
    3. Harga (desc)
    """

    label = (p.get("label") or "").lower()

    prio = 99
    for key, val in PRIORITY_MAP.items():
        if key in label:
            prio = val
            break

    return (
        prio,
        -p["total_days"],
        -p.get("price", 0),
    )


def build_vip_buttons(kode_base, username, promo_used, packages):
    buttons = []

    sorted_packages = sorted(packages, key=_package_priority)

    for idx, p in enumerate(sorted_packages):
        if p.get("is_promo_once") and promo_used:
            continue

        label = p.get("label") or p["paket"]

        # Paket teratas otomatis jadi rekomendasi
        if idx == 0:
            label = f"🔥 {label} — REKOMENDASI"

        buttons.append(
            [
                InlineKeyboardButton(
                    label,
                    callback_data=f"vip_buy:{p['paket']}",
                )
            ]
        )

    buttons.append(
        [
            InlineKeyboardButton(
                "⏳ Nanti Dulu",
                callback_data="vip_later",
            )
        ]
    )

    return InlineKeyboardMarkup(buttons)
