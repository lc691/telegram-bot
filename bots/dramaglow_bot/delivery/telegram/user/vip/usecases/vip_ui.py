import asyncio

from pyrogram.types import CallbackQuery
from pyrogram.enums import ParseMode
from pyrogram.errors import FloodWait, RPCError

from configs.logging_setup import log
from common.utils_new.menu_utils import edit_menu

from ..repository.vip_packages_repo import (
    get_vip_packages_from_db,
    has_used_promo,
)
from ..ui.package_menu import build_vip_buttons


DB_TIMEOUT_SECONDS = 5


async def send_vip_menu(
    event: CallbackQuery,
    display_name: str,
) -> None:
    """
    VIP MENU (UI)
    - EDIT ONLY
    - single-message UI
    """

    user = event.from_user
    user_id = user.id

    log.info("[VIP][MENU] start user_id=%s", user_id)

    try:
        # ===============================
        # DB CALL DENGAN TIMEOUT
        # ===============================
        promo_used = await asyncio.wait_for(
            has_used_promo(user_id),
            timeout=DB_TIMEOUT_SECONDS,
        )

        packages = await asyncio.wait_for(
            get_vip_packages_from_db(),
            timeout=DB_TIMEOUT_SECONDS,
        )

        if not packages:
            await edit_menu(
                event=event,
                text="⚠️ Paket VIP belum tersedia.\nSilakan coba lagi nanti.",
            )
            return

        text = (
            "💎 <b>Pilih Paket VIP</b>\n\n"
            "⚡ Aktif otomatis 10–60 detik\n"
            "📖 Baca <a href='https://t.me/c/3714147269/3'>Panduan Aktivasi Otomatis</a>\n"
            "🎬 Akses penuh semua episode\n\n"
            "👇 Pilih paket terbaik untuk kamu"
        )

        markup = build_vip_buttons(
            f"daftar_short_{user_id}",
            display_name,
            promo_used,
            packages,
        )

        await edit_menu(
            event=event,
            text=text,
            markup=markup,
            parse_mode=ParseMode.HTML,
        )

        log.info(
            "[VIP][MENU] success user_id=%s packages=%s promo_used=%s",
            user_id,
            len(packages),
            promo_used,
        )

    except asyncio.TimeoutError:
        log.error("[VIP][MENU] DB timeout user_id=%s", user_id)
        await edit_menu(
            event=event,
            text="⏳ Sistem sedang sibuk.\nSilakan coba lagi sebentar.",
        )

    except FloodWait as e:
        log.warning(
            "[VIP][MENU] FloodWait user_id=%s wait=%ss",
            user_id,
            e.value,
        )
        await asyncio.sleep(e.value)

    except RPCError as e:
        log.error(
            "[VIP][MENU] Telegram RPC error user_id=%s err=%s",
            user_id,
            e,
        )

    except Exception:
        log.exception("[VIP][MENU] fatal error user_id=%s", user_id)
        await edit_menu(
            event=event,
            text="⚠️ Terjadi kesalahan internal.\nSilakan coba lagi.",
        )
