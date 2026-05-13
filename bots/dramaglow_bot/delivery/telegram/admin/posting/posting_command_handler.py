import asyncio
import re
import time
from html import escape

from pyrogram import Client, filters
from pyrogram.enums import ParseMode
from pyrogram.types import Message

from configs.logging_setup import log
from common.utils.admin_cache import admin_cache

from .....repository.posting.post_show_utils import (
    fetch_show_by_id,
    search_show_by_title,
    parse_batch_ids,
)

from .....usecases.admin.posting.post_show_flow import post_show_flow


GROUP_POSTING = 17
DEFAULT_BATCH_DELAY = 5
MAX_BATCH_SIZE = 100


def register_posting_handler(app: Client):

    @app.on_message(filters.command("pos") & filters.private, group=GROUP_POSTING)
    async def posting_handler(client: Client, message: Message):

        # =====================================================
        # 1️⃣ Validate Admin
        # =====================================================
        if not message.from_user:
            return

        user_id = message.from_user.id

        if not admin_cache.is_admin(user_id):
            return

        input_value = " ".join(message.command[1:]).strip()

        if not input_value:
            await message.reply(
                "❌ Gunakan format:\n"
                "<code>/pos &lt;judul&gt;</code>\n"
                "<code>/pos &lt;id&gt;</code>\n"
                "<code>/pos [1,2,3]</code>\n"
                "<code>/pos [1-5]</code>",
                parse_mode=ParseMode.HTML,
            )
            return

        # =====================================================
        # 2️⃣ Route Mode
        # =====================================================
        if is_batch_mode(input_value):
            await handle_batch_post(client, message, user_id, input_value)
        else:
            await handle_single_post(client, message, user_id, input_value)


# =====================================================
# MODE DETECTION
# =====================================================


def is_batch_mode(text: str) -> bool:
    # Must start with [ ... ]
    return bool(re.match(r"^\[.*\]", text))


# =====================================================
# BATCH MODE
# =====================================================


async def handle_batch_post(client, message, user_id, input_value):

    match = re.match(r"^\[(.*?)\](.*)$", input_value)
    if not match:
        await message.reply("⚠️ Format batch tidak valid.")
        return

    raw_ids = match.group(1)
    extra = match.group(2).strip()

    id_list = parse_batch_ids(raw_ids)

    if not id_list:
        await message.reply("⚠️ Tidak ada ID valid dalam batch.")
        return

    if len(id_list) > MAX_BATCH_SIZE:
        await message.reply(
            f"⚠️ Maksimal batch {MAX_BATCH_SIZE} ID.",
            parse_mode=ParseMode.HTML,
        )
        return

    delay_seconds = DEFAULT_BATCH_DELAY
    if extra.isdigit():
        delay_seconds = int(extra)

    results_summary = []
    start_time = time.perf_counter()

    log.info(
        "[BATCH][START] user=%s total=%s delay=%ss ids=%s",
        user_id,
        len(id_list),
        delay_seconds,
        id_list,
    )

    for index, show_id in enumerate(id_list):

        try:
            result = await post_show_flow(
                client=client,
                show_id=show_id,
            )

            results_summary.append(f"✅ {show_id}")

            log.info(
                "[BATCH][SUCCESS] user=%s show_id=%s msg_id=%s",
                user_id,
                show_id,
                result["message_id"],
            )

        except ValueError as e:
            results_summary.append(f"⚠️ {show_id}")
            log.warning(
                "[BATCH][VALIDATION] user=%s show_id=%s error=%s",
                user_id,
                show_id,
                str(e),
            )

        except Exception:
            results_summary.append(f"❌ {show_id}")
            log.exception(
                "[BATCH][FATAL] user=%s show_id=%s",
                user_id,
                show_id,
            )

        # Sleep only if not last item
        if index < len(id_list) - 1:
            await asyncio.sleep(delay_seconds)

    duration = round(time.perf_counter() - start_time, 2)

    log.info(
        "[BATCH][END] user=%s total=%s duration=%ss",
        user_id,
        len(id_list),
        duration,
    )

    await message.reply(
        "📦 <b>Batch Posting Selesai</b>\n\n"
        + "\n".join(results_summary)
        + f"\n\n⏱ Durasi: {duration}s",
        parse_mode=ParseMode.HTML,
    )


# =====================================================
# SINGLE MODE
# =====================================================


async def handle_single_post(client, message, user_id, input_value):

    start_time = time.perf_counter()

    try:
        # -------------------------------------------------
        # ID Mode
        # -------------------------------------------------
        if input_value.isdigit():
            show_id = int(input_value)

        # -------------------------------------------------
        # Title Mode
        # -------------------------------------------------
        else:
            results = search_show_by_title(input_value)

            if not results:
                raise ValueError("Judul tidak ditemukan di database.")

            if len(results) > 1:
                text = (
                    f"⚠️ Ditemukan beberapa show dengan judul "
                    f"<b>{escape(input_value)}</b>:\n\n"
                )

                for r in results:
                    r_id, r_title, r_series, r_source = r
                    text += (
                        f"🆔 <b>{r_id}</b>\n"
                        f"📺 {escape(r_title)}\n"
                        f"🎞 Series: {r_series}\n"
                        f"🌐 Source: {escape(r_source or '-')}\n\n"
                    )

                text += "Balas dengan:\n<code>/pos &lt;ID&gt;</code>"

                await message.reply(text, parse_mode=ParseMode.HTML)
                return

            show_id = results[0][0]

        # -------------------------------------------------
        # Execute Posting
        # -------------------------------------------------
        result = await post_show_flow(
            client=client,
            show_id=show_id,
        )

        duration = round(time.perf_counter() - start_time, 2)

        await message.reply(
            (
                "✅ <b>Posting Berhasil</b>\n\n"
                f"🎬 <b>Judul</b>  : {escape(result['title'])}\n"
                f"🆔 <b>ID</b>     : {result['show_id']}\n"
                f"📨 <b>Msg ID</b> : {result['message_id']}\n"
                f"🖼 <b>Mode</b>   : {result['mode']}\n"
                f"🔗 <b>Link</b>   : {result['link'] or '-'}\n"
                f"⚡ <b>Durasi</b> : {duration}s"
            ),
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
        )

        log.info(
            "[POSTING][SINGLE] user=%s show_id=%s msg_id=%s mode=%s duration=%ss",
            user_id,
            result["show_id"],
            result["message_id"],
            result["mode"],
            duration,
        )

    except ValueError as e:
        await message.reply(
            f"⚠️ {escape(str(e))}",
            parse_mode=ParseMode.HTML,
        )

        log.warning(
            "[POSTING][VALIDATION] user=%s input='%s' error=%s",
            user_id,
            input_value,
            str(e),
        )

    except Exception:
        log.exception(
            "[POSTING][FATAL] user=%s input='%s'",
            user_id,
            input_value,
        )

        await message.reply(
            "❌ Terjadi kesalahan sistem saat posting.\n" "Silakan cek log server."
        )
