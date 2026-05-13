# #bots\dramaglow_bot\handlers\user\vip_menu\vip_ui.py
from typing import Optional, Union

from pyrogram import Client
from pyrogram.types import CallbackQuery, Message

from common.utils.message_utils import safe_send_or_edit
from configs.logging_setup import log

from ....delivery.telegram.user.vip.repository.vip_packages_repo import (
    format_manual_packages,
    get_vip_packages_from_db,
    has_used_promo,
)
from ....presenters.user.vip.package_menu import build_vip_buttons


async def send_vip_menu(
    client: Client,
    user_id: int,
    username: str,
    event: Optional[Union[Message, CallbackQuery]] = None,
):
    promo_used = await has_used_promo(user_id)
    packages = await get_vip_packages_from_db()
    manual_text = format_manual_packages(packages)

    text = f"""
🔒 **AKSES VIP TERKUNCI**

⚡ **PANDUAN ANTI GAGAL VIP**:
└─ 👉 [Klik di sini](https://t.me/tutorialvip1/22)

═══════✦✧✦═══════
✅ Jangan centang **Anonim**
✍️ Pesan **jangan diubah**
⏱️ Aktif otomatis **10–60 detik**
═══════✦✧✦═══════

💎 **Benefit VIP**
└─ 🔓 Tanpa limit
└─ ▶️ Instan
└─ 🌊 Lancar

{manual_text}

🇮🇩 **Manual Indonesia:** [Klik di sini](https://t.me/+V7vKUz3HFyhiNTBl)
🇲🇾 **Manual Malaysia:** [Klik di sini](https://t.me/+HD4kyH4u7bljMDll)
📩 Admin: @admischelia

⚠️ **Pesan diubah = VIP gagal aktif**
💖 Terima kasih atas dukungannya!
""".strip()

    markup = build_vip_buttons(
        f"daftar_short_{user_id}",
        username,
        promo_used,
        packages,
    )

    try:
        result = await safe_send_or_edit(
            client=client,
            user_id=user_id,
            text=text,
            markup=markup,
            event=event,
        )

        log.info("[VIP_MENU] result=%s user=%s", result, user_id)

    except Exception as e:
        log.error("[VIP_MENU] Gagal kirim menu VIP: %s", e, exc_info=True)
        await client.send_message(
            chat_id=user_id,
            text="❌ Gagal memuat menu VIP. Silakan coba beberapa saat lagi.",
        )
