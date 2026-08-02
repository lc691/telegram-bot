from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from config import VIP_UPGRADE_URL
from configs.logging_setup import log


def build_navigation_keyboard(
    prev_id,
    next_id,
    *,
    is_vip: bool,
    free_remaining: int,
    user_id: int,
    current_id: int,
):
    """
    UI-ONLY navigation keyboard.

    RULES (FINAL):
    - Prev / Next muncul HANYA jika ID tersedia
    - Tidak menentukan boleh/tidaknya akses
    - Tidak tahu PAID / FREE
    - Tidak tahu quota logic
    """

    rows: list[list[InlineKeyboardButton]] = []
    log_flags: list[str] = []

    # ==================================================
    # 1️⃣ NAV ROW (PURE ID-BASED)
    # ==================================================
    nav_row: list[InlineKeyboardButton] = []

    if prev_id is not None:
        nav_row.append(
            InlineKeyboardButton(
                "⏮️ Prev",
                callback_data=f"navigate|{current_id}|prev",
            )
        )
        log_flags.append("Prev=ON")
    else:
        log_flags.append("Prev=OFF")

    if next_id is not None:
        nav_row.append(
            InlineKeyboardButton(
                "⏭️ Next",
                callback_data=f"navigate|{current_id}|next",
            )
        )
        log_flags.append("Next=ON")
    else:
        log_flags.append("Next=OFF")

    if nav_row:
        rows.append(nav_row)

    # ==================================================
    # 2️⃣ UPGRADE ROW (UX ONLY)
    # ==================================================
    if not is_vip:
        rows.append(
            [
                InlineKeyboardButton(
                    "💎 Upgrade VIP",
                    url=VIP_UPGRADE_URL,
                )
            ]
        )
        log_flags.append("Upgrade=ON")
    else:
        log_flags.append("Upgrade=OFF")

    # ==================================================
    # 3️⃣ FINAL SAFETY
    # ==================================================
    log.debug(
        "[NAV-KEYBOARD] user=%s | %s | rows=%d",
        user_id,
        " | ".join(log_flags),
        len(rows),
    )

    return InlineKeyboardMarkup(rows) if rows else None
