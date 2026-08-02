from pyrogram import Client, filters
from pyrogram.errors import MessageNotModified
from pyrogram.types import CallbackQuery

from configs.logging_setup import log

from apps.drac1n_bot.delivery.telegram.admin.leaderboard.usecases.leaderboard_params import (
    parse_leaderboard_callback
)

from apps.drac1n_bot.delivery.telegram.admin.leaderboard.usecases.leaderboard_flow import (
    show_leaderboard
)
from apps.drac1n_bot.delivery.telegram.admin.leaderboard.presenters.date_keyboard import (
    month_picker_keyboard,
    day_picker_keyboard,
)


GROUP = 5


def register_leaderboard_callback(app: Client):

    # ======================================================
    # CALLBACK: Leaderboard (period + date + page)
    # ======================================================
    @app.on_callback_query(filters.regex(r"^vip_lb:"), group=GROUP)
    async def vip_leaderboard_callback(_: Client, callback: CallbackQuery):
        user = callback.from_user
        message = callback.message

        if not user or not message:
            await callback.answer("Aksi tidak valid", show_alert=True)
            return

        params = parse_leaderboard_callback(callback.data)
        if not params:
            await callback.answer("Callback tidak dikenali", show_alert=True)
            return

        log.debug(
            "[LEADERBOARD][CALLBACK] user_id=%s period=%s date=%s page=%s",
            user.id,
            params.period,
            params.date,
            params.page,
        )

        try:
            await show_leaderboard(
                client=callback._client,
                event=callback,
                period=params.period,
                page=params.page,
                date=params.date,
            )
            # show_leaderboard sudah handle edit/reply
            await callback.answer()

        except MessageNotModified:
            # expected: klik page yang sama
            await callback.answer()

        except Exception:
            log.exception("[LEADERBOARD][CALLBACK] ❌ Error")
            await callback.answer(
                "⚠️ Gagal memuat leaderboard",
                show_alert=True,
            )

    # ======================================================
    # CALLBACK: 📅 Date Picker
    # ======================================================
    @app.on_callback_query(filters.regex(r"^vip_date:"), group=GROUP)
    async def vip_date_callback(_: Client, callback: CallbackQuery):
        user = callback.from_user
        message = callback.message

        if not user or not message:
            await callback.answer("Aksi tidak valid", show_alert=True)
            return

        try:
            _, action, value = callback.data.split(":", 2)

            log.debug(
                "[LEADERBOARD][DATE] user_id=%s action=%s value=%s",
                user.id,
                action,
                value,
            )

            # -----------------------------
            # Month picker
            # vip_date:month:YYYY-MM
            # -----------------------------
            if action == "month":
                await message.edit_text(
                    "📅 Pilih Bulan",
                    reply_markup=month_picker_keyboard(value),
                )

            # -----------------------------
            # Day picker
            # vip_date:day:YYYY-MM
            # -----------------------------
            elif action == "day":
                await message.edit_text(
                    f"📅 Pilih Tanggal ({value})",
                    reply_markup=day_picker_keyboard(value),
                )

            # -----------------------------
            # Date selected → back to leaderboard
            # vip_date:select:YYYY-MM-DD
            # -----------------------------
            elif action == "select":
                await show_leaderboard(
                    client=callback._client,
                    event=callback,
                    period="daily",
                    page=1,
                    date=value,
                )

            await callback.answer()

        except MessageNotModified:
            await callback.answer()

        except Exception:
            log.exception("[LEADERBOARD][DATE] ❌ Error")
            await callback.answer(
                "⚠️ Gagal memilih tanggal",
                show_alert=True,
            )
