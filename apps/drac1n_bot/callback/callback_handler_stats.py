from pyrogram import Client, filters
from pyrogram.types import CallbackQuery

from shared.utils.admin_cache import admin_cache
from configs.logging_setup import log

from apps.drac1n_bot.callback.stats.film_detail import show_film_detail
from apps.drac1n_bot.callback.stats.film_selector import show_film_selector
from apps.drac1n_bot.callback.stats.top_films import show_top_films
from apps.drac1n_bot.callback.stats.top_users import show_top_users
from apps.drac1n_bot.callback.stats.vip_vs_free import show_vip_vs_free

STATS_REGEX = r"^stat_(top_films|top_users|vip_vs_free|detail_menu)$"


def register_stats_callback(app: Client):
    @app.on_callback_query(filters.regex(STATS_REGEX))
    async def handle_stat_callbacks(client: Client, callback_query: CallbackQuery):
        user_id = callback_query.from_user.id
        log.info(f"Callback diterima: {callback_query.data} dari user {user_id}")

        if user_id not in admin_cache:
            await callback_query.answer(
                "❌ Menu ini hanya untuk admin.", show_alert=True
            )
            return

        data = callback_query.data

        if data == "stat_top_films":
            await show_top_films(callback_query)
        elif data == "stat_top_users":
            await show_top_users(callback_query)
        elif data == "stat_vip_vs_free":
            await show_vip_vs_free(callback_query)
        elif data == "stat_detail_menu":
            await show_film_selector(client, callback_query, page=1)
        else:
            log.warning(f"Callback tidak dikenal: {data}")
            await callback_query.answer("Menu tidak ditemukan.", show_alert=True)

    @app.on_callback_query(filters.regex(r"^stat_detail\|(.+?)(\|\d+)?$"))
    async def show_film_detail_callback(client: Client, callback_query: CallbackQuery):
        user_id = callback_query.from_user.id
        if user_id not in admin_cache:
            await callback_query.answer(
                "❌ Menu ini hanya untuk admin.", show_alert=True
            )
            return

        parts = callback_query.data.split("|")
        slug = parts[1]
        page = parts[2] if len(parts) > 2 else "1"

        log.info(
            f"Menampilkan detail film untuk slug: {slug} (halaman {page}) oleh user {user_id}"
        )
        await show_film_detail(client, callback_query, f"{slug}|{page}")

    @app.on_callback_query(filters.regex(r"^show_film_selector\|(\d+)$"))
    async def show_film_selector_pagination(
        client: Client, callback_query: CallbackQuery
    ):
        user_id = callback_query.from_user.id
        if user_id not in admin_cache:
            await callback_query.answer(
                "❌ Menu ini hanya untuk admin.", show_alert=True
            )
            return

        page_str = callback_query.data.split("|", 1)[1]
        page = int(page_str)
        await show_film_selector(client, callback_query, page=page)
