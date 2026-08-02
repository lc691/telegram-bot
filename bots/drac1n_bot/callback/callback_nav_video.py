from pyrogram import filters
from datetime import datetime, timezone

from configs.trace import set_trace_id, reset_trace_id
from configs.logging_setup import log
from common.utils.admin_cache import admin_cache

from db.connect import get_dict_cursor
from bots.drac1n_bot.delivery.telegram.user.services.user_service import UserAccessService
from bots.drac1n_bot.delivery.telegram.user.file.services.cache import get_navigation_info_cached
from bots.drac1n_bot.delivery.telegram.user.file.usecases.access_file_flow import access_file_flow


def register_nav_video_callback(app):
    @app.on_callback_query(filters.regex(r"^navigate\|\d+\|(next|prev)$"))
    async def handle_file_navigation(client, query):
        user = query.from_user
        if not user:
            return await query.answer()

        user_id = user.id
        is_admin = admin_cache.is_admin(user_id)

        # ==================================================
        # ✅ TRACE SETUP
        # ==================================================
        now_utc = datetime.now(timezone.utc)
        trace_id = (
            f"S-{user_id}-"
            f"{now_utc.strftime('%Y%m%d%H%M%S')}"
            f"{int(now_utc.microsecond / 1000):03d}"
        )
        token = set_trace_id(trace_id)

        try:
            # ==================================================
            # 1️⃣ PARSE CALLBACK DATA
            # ==================================================
            try:
                _, current_file_id, direction = query.data.split("|", 2)
                current_file_id = int(current_file_id)
            except Exception:
                return await query.answer(
                    "Invalid navigation action",
                    show_alert=True,
                )

            log.info(
                "[NAV] start user=%s file=%s dir=%s admin=%s",
                user_id,
                current_file_id,
                direction,
                is_admin,
            )

            # ==================================================
            # 2️⃣ LOAD USER ACCESS STATE (VIP / FREE)
            # ==================================================
            _, is_vip, _ = await UserAccessService.check_access(
                user_id,
                is_admin,
            )

            # ==================================================
            # 3️⃣ RESOLVE SHOW ID
            # ==================================================
            with get_dict_cursor() as (cur, _):
                cur.execute(
                    "SELECT show_id FROM files WHERE id=%s",
                    (current_file_id,),
                )
                row = cur.fetchone()

            if not row:
                return await query.answer(
                    "❌ File tidak ditemukan.",
                    show_alert=True,
                )

            show_id = row["show_id"]

            # ==================================================
            # 4️⃣ RESOLVE TARGET FILE (🔥 POLICY-AWARE NAV 🔥)
            # ==================================================
            nav = get_navigation_info_cached(
                show_id,
                current_file_id,
                is_vip=is_vip,
            )

            if not nav:
                return await query.answer(
                    "❌ Navigasi tidak tersedia.",
                    show_alert=True,
                )

            target_file_id = nav["next_id"] if direction == "next" else nav["prev_id"]

            if not target_file_id:
                return await query.answer(
                    "🚫 Tidak ada file di arah ini.",
                    show_alert=True,
                )

            # ==================================================
            # 5️⃣ DELEGATE TO ACCESS FLOW (FINAL GATE)
            # ==================================================
            await access_file_flow(
                client=client,
                message=query.message,
                user_id=user_id,
                access_hash=None,  # ⬅️ IMPORTANT
                file_id=target_file_id,  # ⬅️ akses via ID
                is_admin=is_admin,
                edit=True,
            )

            await query.answer()

            log.info(
                "[NAV] done user=%s from=%s to=%s",
                user_id,
                current_file_id,
                target_file_id,
            )

        except Exception:
            log.exception(
                "[NAV] error user=%s data=%s",
                user_id,
                query.data,
            )
            await query.answer(
                "❗ Terjadi kesalahan saat navigasi.",
                show_alert=True,
            )

        finally:
            reset_trace_id(token)
