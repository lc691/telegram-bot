import asyncio

from configs.bots_config import BOT_CONFIG
from configs.logging_setup import setup_logging

setup_logging()

# Ambil factory dari konfigurasi bot utama
drac1n_config = BOT_CONFIG["drac1n_bot"]
create_app_func = drac1n_config["factory"]


async def main():
    app = await create_app_func()  # ⬅️ WAJIB pakai await
    print("✅ Bot playground aktif")

    # ================= UJI COBA =================
    # 🧪 Uji kirim notifikasi ke admin
    # await log_to_admin(app, "🧪 Tes notifikasi error dari playground pakai drac1n_bot!")
    # await notify_vip_from_logs(app, bot_name="drac1n")  # ← pastikan nama sesuai log
    # reminder_task = asyncio.create_task(reminder_loop(app))
    # ================= UJI COBA =================

    await app.stop()
    print("✅ Bot playground dihentikan")


if __name__ == "__main__":
    asyncio.run(main())
