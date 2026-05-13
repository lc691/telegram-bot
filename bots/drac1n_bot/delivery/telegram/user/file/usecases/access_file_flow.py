from configs.logging_setup import log
from ...vip.helpers.helper import (
    _reply_upgrade_free,
    _reply_upgrade_paid,
)
from ..services.file_service import increment_view_count
from ..services.sender import send_with_navigation
from ...services.user_service import UserAccessService
from db.connect import get_dict_cursor


async def access_file_flow(
    *,
    client,
    message,
    user_id: int,
    is_admin: bool,
    edit: bool = False,
    access_hash: str | None = None,
    file_id: int | None = None,
):
    """
    FINAL FILE ACCESS FLOW
    Policy:
    - FREE / PAID ditentukan HANYA oleh files.is_paid
    - Kuota hanya berlaku untuk FREE
    - PAID absolut VIP/Admin
    """

    # ==================================================
    # 0️⃣ RESOLVE FILE (SINGLE SOURCE)
    # ==================================================
    with get_dict_cursor() as (cur, _):

        # Navigation path
        if file_id is not None:
            cur.execute(
                """
                SELECT
                    id,
                    is_paid,
                    free_hash,
                    paid_hash
                FROM files
                WHERE id = %s
                """,
                (file_id,),
            )

        # Start / search path
        else:
            cur.execute(
                """
                SELECT
                    id,
                    is_paid,
                    free_hash,
                    paid_hash
                FROM files
                WHERE free_hash = %s
                   OR paid_hash = %s
                """,
                (access_hash, access_hash),
            )

        file = cur.fetchone()

    if not file:
        return await message.reply_text("❌ File tidak valid.")

    file_db_id = file["id"]
    is_paid_file = file["is_paid"] is True
    free_hash = file["free_hash"]
    paid_hash = file["paid_hash"]

    # hash yang dipakai untuk statistik
    stat_hash = paid_hash if is_paid_file else free_hash

    # ==================================================
    # 1️⃣ USER ACCESS CHECK
    # ==================================================
    allowed, is_vip, free_remaining = await UserAccessService.check_access(
        user_id,
        is_admin,
    )

    if not allowed:
        return await _reply_upgrade_free(message)

    # ==================================================
    # 🔒 HARD POLICY (PAID ABSOLUT)
    # ==================================================
    if is_paid_file and not is_vip and not is_admin:
        log.info(
            "[ACCESS] BLOCK PAID user=%s vip=%s admin=%s file=%s",
            user_id,
            is_vip,
            is_admin,
            file_db_id,
        )
        return await _reply_upgrade_paid(message)

    # ==================================================
    # 2️⃣ CONSUME QUOTA (FREE ONLY)
    # ==================================================
    before_quota = free_remaining

    if not is_paid_file and not is_vip and not is_admin:
        remaining = await UserAccessService.consume_free_quota_atomic(user_id)
        if remaining is None:
            return await _reply_upgrade_free(message)
        free_remaining = remaining

    # ==================================================
    # 🔥 SINGLE ACCESS LOG (MINIM IO)
    # ==================================================
    role = "A" if is_admin else "V" if is_vip else "F"
    log.info(
        "[ACCESS] u=%s r=%s paid=%d q=%s->%s e=%d",
        user_id,
        role,
        int(is_paid_file),
        before_quota if role == "F" else "-",
        free_remaining if role == "F" else "-",
        int(edit),
    )

    # ==================================================
    # 3️⃣ ANALYTICS VIEW
    # ==================================================
    try:
        increment_view_count(stat_hash)
    except Exception:
        log.exception("[STATS] increment_view_count failed")

    # ==================================================
    # 4️⃣ SEND FILE
    # ==================================================
    try:
        await send_with_navigation(
            message=message,
            file_db_id=file_db_id,
            user_id=user_id,
            is_admin=is_admin,
            is_vip=is_vip,
            free_remaining=free_remaining,
            edit=edit,
        )
    except Exception:
        log.exception("[FILE_ACCESS] send failed")
        await message.reply_text("❗ Gagal mengirim file.")
