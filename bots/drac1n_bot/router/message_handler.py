# === handlers/text_router/message_router.py ===

import re

from pyrogram import Client, filters
from pyrogram.types import Message

from bots.drac1n_bot.delivery.telegram.user.services.channel_repository import save_required_channel
from bots.drac1n_bot.ui.dashboard import send_dashboard
from common.utils.admin_cache import admin_cache
from common.utils.admin_state_manager import AdminStateManager
from common.utils.state_helper import cancel_all_states, should_cancel_state_on_command
from configs.logging_setup import log
from db.chanel_management import discard_user, is_user_adding

from .admin_text_router import handle_admin_text
from .request_autocomplete_handler import handle_autocomplete_source
from .request_text_handler import handle_request_text
from .search_text_handler import handle_search_text
from .vip_text_router import handle_vip_text

DEFAULT_USER_GROUP = 5

# ✅ Daftar kata-kata / pola yang dilarang (kasar, porno, SARA, provokatif)
FORBIDDEN_PATTERNS = [
    # Agama / SARA / etnis
    r"\bagama\b",
    r"\b(islam|kristen|budha|hindu|yahudi|nasrani|syiah|atheis|zionis|israel|palestina)\b",
    r"\bkafir\b",
    r"\bpribumi\b",
    r"\bnonpribumi\b",
    r"\b(hitam|putih|cina|arab|jawa|batak|sunda|minangkabau|madura|dayak|papua|minoritas|mayoritas)\b",
    r"\bsalib\b",
    r"\bustadz\b",
    r"\bpendeta\b",
    r"\bsara\b",
    r"\brasis\b",
    r"\bteroris\b",
    r"\bjihad\b",
    # Kata-kata kasar / porno / seksual
    r"\bpeli\b",
    r"\bkontol\b",
    r"\bmemek\b",
    r"\bmemew\b",
    r"\bjembut\b",
    r"\bngentot\b",
    r"\bsex\b",
    r"\bporno\b",
    r"\bbugil\b",
    r"\bbokep\b",
    r"\bcrot\b",
    r"\bpepek\b",
    r"\bbencong\b",
    r"\blonte\b",
    r"\btontonan\s+dewasa\b",
    # Kata-kata menghina / provokatif
    r"\bidiot\b",
    r"\bbrengsek\b",
    r"\bangsat\b",
    r"\bmonyet\b",
    r"\bsetan\b",
    r"\bpenipu\b",
    r"\bgoblok\b",
    r"\bkeparat\b",
    r"\bmampus\b",
    r"\bterlaknat\b",
    r"\bmiskin\b",
    r"\bgila\b",
    r"\bpembodohan\b",
    r"\banjing\b",
    r"\btolol\b",
    # Politik / sensitif
    r"\bkorupsi\b",
    r"\bpartai\b",
    r"\bpolitik\b",
    r"\brevolusi\b",
    r"\bprabowo\b",
    r"\bjokowi\b",
    r"\bcapres\b",
]

# ✅ Buat list command dikecualikan supaya lebih rapih
EXCLUDED_COMMANDS = [
    "start",
    "donasi",
    "vip",
    "status",
    "dashboard",
    "ujian",
    "riwayat",
    "cari",
    "request",
    "jawaban",
    "channel",
    "broadcast",
    "trial",
    "benefit",
    "commands",
    "redeemvip",
    "tespoll",
    "post_show",
    "update_thumbnail",
    "requestsource",
    "pos",
    "voucher",
    "genre",
    "r_wd",
    "r_link",
    "r_stats",
    "rebuild_cache",
    "topvip",
]


# ✅ Fungsi cek kata terlarang
def contains_forbidden_word(text: str) -> bool:
    text_lower = text.lower()
    return any(re.search(pattern, text_lower) for pattern in FORBIDDEN_PATTERNS)


def register_text_router_handler(app: Client):
    """
    Registrasi router handler untuk text message (private & grup)
    yang bukan command tertentu.
    """

    async def message_entrypoint(client: Client, message: Message):
        user = message.from_user
        if not user:
            log.warning("[ENTRY] Pesan tidak memiliki from_user.")
            return

        if user.is_bot:
            log.info(f"[SKIP] Pesan dari bot lain diabaikan: {user.id}")
            return

        user_id = user.id
        text = message.text.strip() if message.text else ""

        # 🔴 CEK KATA TERLARANG
        # ✅ Cek apakah kata terlarang muncul dalam teks, tapi abaikan jika itu judul show
        def contains_forbidden_word(text: str, db_conn) -> bool:
            text_lower = text.lower()

            # 1️⃣ Cek dulu apakah teks mengandung kata terlarang
            matches = [p for p in FORBIDDEN_PATTERNS if re.search(p, text_lower)]
            if not matches:
                return False

            # 2️⃣ Ambil semua judul dari tabel shows
            with db_conn.cursor() as cur:
                cur.execute("SELECT LOWER(title) FROM shows")
                titles = [row[0] for row in cur.fetchall()]

            # 3️⃣ Kalau teks sama persis dengan salah satu judul, abaikan
            for title in titles:
                if title in text_lower:
                    return False  # abaikan, karena termasuk judul show

            # 4️⃣ Kalau tidak ada kecocokan dengan judul show → dianggap terlarang
            return True

        # ✅ Lanjutkan alur FSM & handler lain
        log.info(f"[ENTRY] Pesan diterima dari {user_id}: {text}")

        try:
            # === CHANNEL ADD FLOW ===
            if is_user_adding(user_id):
                try:
                    username = text
                    added_by = user.username or str(user_id)
                    save_required_channel(username, added_by)
                    await message.reply_text("✅ Channel berhasil ditambahkan!")
                except Exception as e:
                    log.error(f"❌ [CHANNEL_ADD] Gagal: {e}", exc_info=True)
                    await message.reply_text("❌ Gagal menambahkan channel.")
                finally:
                    discard_user(user_id)
                    return await send_dashboard(source=message, is_callback=False)

            # === INIT STATE ===
            is_admin = admin_cache.is_admin(user_id)
            log.debug(f"[STATE] is_admin={is_admin} untuk user {user_id}")

            # === CANCEL FLOW ===
            if should_cancel_state_on_command(text):
                log.info(f"[CANCEL] Semua state dibatalkan oleh {user_id}")
                cancel_all_states(user_id)
                return await send_dashboard(source=message, is_callback=False)

            # === ADMIN TEXT FSM ===
            if await handle_admin_text(client, message, is_admin):
                return

            # === VIP TEXT FSM ===
            if await handle_vip_text(client, message, is_admin):
                return

            # === REQUEST TEXT FSM ===
            if await handle_request_text(client, message):
                return

            # === SEARCH TEXT FSM ===
            if await handle_search_text(client, message):
                return

            # === CEK FSM ADMIN ===
            admin_state = AdminStateManager(user_id)
            if admin_state.has_active_step():
                log.info(f"[ADMIN_FLOW] FSM aktif, skip fallback untuk {user_id}")
                return

            # === AUTOCOMPLETE SOURCE ===
            if await handle_autocomplete_source(client, message):
                return

            # === FALLBACK ===
            log.info(f'[NO_ACTION] Tidak ada aksi terdeteksi untuk {user_id}: "{text}"')

        except Exception as e:
            log.error(
                f"❌ [ERROR] Gagal proses pesan user {user_id}: {e}", exc_info=True
            )
            await message.reply_text(
                "⚠️ Maaf, terjadi kesalahan teknis. Coba lagi sebentar ya!"
            )

    # Handler untuk private chat
    @app.on_message(
        filters.private
        & filters.text
        & ~filters.command(EXCLUDED_COMMANDS)
        & ~filters.me,
        group=DEFAULT_USER_GROUP,
    )
    async def private_message_entrypoint(client: Client, message: Message):
        await message_entrypoint(client, message)

    # Handler untuk grup
    @app.on_message(
        filters.group
        & filters.text
        & ~filters.command(EXCLUDED_COMMANDS)
        & ~filters.me,
        group=DEFAULT_USER_GROUP,
    )
    async def group_message_entrypoint(client: Client, message: Message):
        await message_entrypoint(client, message)


def register_catch_all_handler(app):
    @app.on_message(
        (
            (filters.private & filters.text & ~filters.regex(r"^/"))
            | (filters.group & filters.text & ~filters.regex(r"^/"))
        ),
        group=99,
    )
    async def catch_all(client, message: Message):
        text = message.text or message.caption or ""
        chat_type = str(message.chat.type).replace("ChatType.", "").upper()

        if message.from_user:
            markers = {
                "PRIVATE": "🟢",
                "GROUP": "🔵",
                "SUPERGROUP": "🟣",
            }
            marker = markers.get(chat_type, "📩")
            log.info(
                f"{marker} [CATCH-ALL][{chat_type}] "
                f"User {message.from_user.id} (@{message.from_user.username}) "
                f"pesan: {text!r}"
            )
            return

        if message.sender_chat:
            log.info(
                f"🟡 [CATCH-ALL][CHANNEL] "
                f"Channel {message.sender_chat.id} "
                f"nama={message.sender_chat.title!r} "
                f"pesan: {text!r}"
            )
            return

        log.info(f"⚙️ [CATCH-ALL][SERVICE] Pesan sistem: {message}")
