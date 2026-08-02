import math

from datetime import datetime, timedelta

from apps.dramaglow_bot.utils.vip_keyboard_factory import vip_stats_keyboard
from shared.bot_utils import get_table_name
from shared.utils.escape_markdown import escape_md
from configs.logging_setup import log
from database.connection import get_db_cursor


def get_vip_stats_message(source: str, jenis: str, page: int):

    try:
        today = datetime.today().date()

        # Normalisasi alias jenis
        if jenis.startswith("vip-") or jenis == "vip-all":
            jenis = "vip"
        elif jenis not in ("vip", "donation"):
            raise ValueError(f"Jenis tidak dikenali: {jenis}")

        with get_db_cursor() as (cursor, _):
            table_name = get_table_name(source)

            if jenis == "vip":
                cursor.execute(
                    f"""
                    SELECT user_id, vip_expired, first_name, username, vip_purchases
                    FROM {table_name}
                    WHERE is_vip = TRUE
                    ORDER BY vip_expired DESC NULLS LAST
                """
                )

                results = cursor.fetchall()
                title = f"👑 **Daftar VIP Aktif — {escape_md(source.title())}**"
                no_data_msg = "_Belum ada member VIP aktif._"

                aktif = hampir_habis = kadaluarsa = 0
                for row in results:
                    expired = row[1]
                    expired_date = (
                        expired.date() if isinstance(expired, datetime) else expired
                    )
                    if not expired_date:
                        continue
                    if expired_date > today + timedelta(days=7):
                        aktif += 1
                    elif expired_date >= today:
                        hampir_habis += 1
                    else:
                        kadaluarsa += 1

            elif jenis == "donation":
                cursor.execute(
                    """
                    SELECT email, amount, message, timestamp
                    FROM donation_log
                    WHERE type = 'vip' AND source_bot = %s
                    ORDER BY timestamp DESC
                    """,
                    (source,),
                )
                results = cursor.fetchall()
                title = f"💰 **Log Donasi VIP — {escape_md(source.title())}**"
                no_data_msg = "_Belum ada donasi VIP tercatat._"

        # Pagination
        ITEMS_PER_PAGE = 5
        total = len(results)
        max_page = max(0, math.ceil(total / ITEMS_PER_PAGE) - 1)
        page = max(0, min(page, max_page))
        current_items = results[page * ITEMS_PER_PAGE : (page + 1) * ITEMS_PER_PAGE]

        # Buat pesan
        msg = f"{title}\n"
        if jenis == "vip":
            msg += (
                f"👥 **Total VIP Aktif:** `{total}`\n"
                f"✅ Aktif: `{aktif}` | ⚠️ Hampir Habis: `{hampir_habis}` | ❌ Kadaluarsa: `{kadaluarsa}`\n"
            )
        msg += f"_Halaman {page + 1} dari {max_page + 1}_\n"
        msg += "━━━━━━━━━━━━━━━\n\n"

        if not current_items:
            msg += no_data_msg
        elif jenis == "vip":
            for user_id, expired, first_name, username, purchases in current_items:
                purchases = purchases or 0
                expired_date = (
                    expired.date() if isinstance(expired, datetime) else expired
                )
                expired_str = expired_date.strftime("%d %b %Y") if expired_date else "-"
                status = (
                    (
                        "✅ **Aktif**"
                        if expired_date > today + timedelta(days=7)
                        else (
                            "⚠️ **Hampir habis**"
                            if expired_date >= today
                            else "❌ **Kadaluarsa**"
                        )
                    )
                    if expired_date
                    else "❓ Tidak diketahui"
                )

                mention = (
                    f"[{escape_md(first_name)}](tg://user?id={user_id})"
                    if first_name
                    else f"`{user_id}`"
                )
                uname = f" (@{escape_md(username)})" if username else ""

                msg += (
                    f"{status} | {mention}{uname}\n"
                    f"🆔 `{user_id}`\n"
                    f"⏳ **Hingga:** `{expired_str}`\n"
                    f"⭐️ **Jumlah Pembelian VIP:** `{purchases}`\n"
                    f"━━━━━━━━━━━━━━━\n"
                )

        else:  # donation
            for email, amount, message, timestamp in current_items:
                ts_str = (
                    timestamp.strftime("%d %b %Y %H:%M:%S")
                    if isinstance(timestamp, datetime)
                    else str(timestamp)
                )
                msg += (
                    f"📧 **Email:** `{email}`\n"
                    f"💸 **Jumlah:** `{amount}`\n"
                    f"📝 **Pesan:** `{message}`\n"
                    f"🕒 **Waktu:** `{ts_str}`\n"
                    f"━━━━━━━━━━━━━━━\n"
                )

        return msg.strip(), vip_stats_keyboard(source, jenis, page, max_page)

    except Exception as e:
        log.exception(f"[VIP STATS] Gagal membuat pesan statistik: {e}")
        raise
