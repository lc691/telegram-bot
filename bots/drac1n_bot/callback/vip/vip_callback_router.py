from pyrogram import Client, filters
from pyrogram.types import CallbackQuery

from common.utils.vip_state_manager import VipStateManager  # pastikan path sesuai

from ..vip.exact_routes import vip_exact_routes
from ..vip.regex_routes import vip_regex_routes


def register_vip_router(app: Client):
    @app.on_callback_query(filters.regex(r"^vip_"))
    async def handle_vip_routes(client: Client, callback_query: CallbackQuery):
        callback_data = callback_query.data
        user_id = callback_query.from_user.id

        # 1️⃣ Buat instance VipStateManager per user
        state = VipStateManager(user_id, source_bot="drac1n")

        # 2️⃣ Cek exact routes
        if callback_data in vip_exact_routes:
            handler = vip_exact_routes[callback_data]
            print(f"[VIP Router] Exact match: {callback_data}")
            await handler(client, callback_query, state)
            return

        # 3️⃣ Cek regex routes
        for pattern, handler in vip_regex_routes.items():
            if pattern.match(callback_data):
                print(f"[VIP Router] Regex match: {pattern.pattern}")
                await handler(client, callback_query, state)
                return

        # # 4️⃣ Tidak ditemukan
        # print(f"[VIP Router] Tidak ada handler untuk: {callback_data}")
        # await callback_query.answer("❌ Aksi tidak dikenali", show_alert=True)
