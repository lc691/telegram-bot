# # services/files/sender.py

from configs.logging_setup import log

from .cache import get_navigation_info_cached
from .navigation import build_navigation_keyboard
from .repository import get_file
from .send_media import send_media


async def send_with_navigation(
    *,
    message,
    file_db_id: int,
    user_id: int,
    is_admin: bool,
    is_vip: bool,
    free_remaining: int,
    edit: bool = False,
):
    """
    PURE DELIVERY LAYER

    Kontrak KERAS:
    - Fungsi ini DIPANGGIL HANYA SETELAH access_file_flow
    - TIDAK melakukan access check
    - TIDAK mengubah quota
    - TIDAK menentukan boleh/tidaknya akses
    - Aman untuk edit / replay / retry

    Tugas:
    1. Resolve file
    2. Resolve navigation
    3. Build caption
    4. Build keyboard
    5. Send / edit media
    """

    # NOTE:
    # Jangan tambahkan access / quota logic di sini.
    # Semua policy ada di access_file_flow.

    # ==================================================
    # 1️⃣ FILE RESOLUTION
    # ==================================================
    file = get_file(file_db_id)
    if not file:
        return await message.reply_text("❌ File tidak ditemukan.")

    # ==================================================
    # 2️⃣ NAVIGATION RESOLUTION
    # ==================================================
    nav = get_navigation_info_cached(
        file["show_id"],
        file_db_id,
        is_vip=is_vip,
    )

    if not nav:
        return await message.reply_text("❌ Navigasi tidak tersedia.")

    # ==================================================
    # 3️⃣ CAPTION BUILD
    # ==================================================
    post_link = None
    if file.get("channel_username") and file.get("message_id"):
        post_link = (
            f"https://t.me/" f"{file['channel_username']}/" f"{file['message_id']}"
        )

    name = file["file_name"]
    name_without_ext = name.rsplit(".", 1)[0] if "." in name else name

    if is_admin:
        access_label = "Admin"
    elif is_vip:
        access_label = "VIP"
    else:
        access_label = f"Free ({free_remaining})"

    caption_lines = [
        f"🎬 <b>{name_without_ext}</b>",
        f"✅ Akses: <b>{access_label}</b>",
        f"📂 Part {nav['position']} / {nav['total']}",
        "================",
    ]

    if post_link:
        caption_lines.append(f"🔗 <a href='{post_link}'>Post Drama</a>")

    caption = "\n".join(caption_lines)

    # ==================================================
    # 4️⃣ KEYBOARD BUILD (UI ONLY)
    # ==================================================
    keyboard = build_navigation_keyboard(
        prev_id=nav.get("prev_id"),
        next_id=nav.get("next_id"),
        is_vip=is_vip,
        free_remaining=free_remaining,
        user_id=user_id,
        current_id=file_db_id,
    )

    # ==================================================
    # 5️⃣ SEND / EDIT MEDIA (SINGLE EXIT)
    # ==================================================
    try:
        await send_media(
            message,
            file=file,
            caption=caption,
            keyboard=keyboard,
            edit=edit,
        )
    except Exception:
        log.exception("[SEND] primary failed, fallback to reply")

        await send_media(
            message,
            file=file,
            caption=caption,
            keyboard=None,
            edit=False,
        )

    file_name = file["file_name"]

    log.info(
        "[SEND] user=%s file=%s part=%s/%s name='%s' vip=%s",
        user_id,
        file_db_id,
        nav["position"],
        nav["total"],
        file_name,
        is_vip,
    )
