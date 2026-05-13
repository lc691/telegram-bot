import hashlib

from pyrogram.enums import ParseMode
from pyrogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InlineQueryResultArticle,
    InputTextMessageContent,
)
from configs.logging_setup import log
from ..config.settings import DEFAULT_THUMBNAIL_URL
from ..usecases.inline_search.types import ResultKind, ShowRow, SearchResult
from ..utils.text_highlight import highlight_query_adaptive, safe
from ..utils.mood_bot import get_bot_mood


# =====================================================
# 🧱 PUBLIC BUILDER
# =====================================================
def build_inline_results(*, result: SearchResult, query: str, offset: int):
    if result.kind == ResultKind.FALLBACK:
        return [_build_no_result_banner(query)]

    results = []
    rows = result.rows or []

    for i, row in enumerate(rows):
        unique_id = f"{result.kind.value}_{row[0]}_{row[3]}_{offset + i}"
        results.append(
            build_show_card(
                row=row,
                kind=result.kind,
                query=query,
                unique_id=unique_id,
            )
        )
    return results


def build_show_card(
    *,
    row: ShowRow,
    kind: ResultKind,
    query: str,
    unique_id: str,
) -> InlineQueryResultArticle:
    """
    Build satu kartu inline untuk satu show.
    """

    sid, title, thumb, channel_username, message_id = row
    # 🔍 DEBUG LOG DI SINI
    log.info(
        "[INLINE_CARD] show=%s channel=%s message=%s",
        sid,
        channel_username,
        message_id,
    )

    safe_title = safe(title)
    # ==================================================
    # LINK TARGET
    # ==================================================
    if message_id and channel_username:
        link_text = f"https://t.me/{channel_username}/{message_id}"
    else:
        link_text = "📭 File belum tersedia"

    # ==================================================
    # TITLE (INLINE LIST)
    # ==================================================
    if kind == ResultKind.SEARCH and query:
        display_title = highlight_query_adaptive(
            title,
            query,
            device="mobile",  # inline Telegram = mobile density
        )
    else:
        display_title = safe_title

    # ==================================================
    # MESSAGE TEXT (CONSISTENT)
    # ==================================================
    message_title = display_title if kind == ResultKind.SEARCH else safe_title

    # ==================================================
    # DESCRIPTION (INLINE LIST)
    # ==================================================
    base_desc = _DESC_MAP.get(kind, "Drama")
    description = f"ID: {sid} | {base_desc}"

    return InlineQueryResultArticle(
        id=unique_id,
        title=display_title,
        description=description,
        thumb_url=thumb or DEFAULT_THUMBNAIL_URL,
        input_message_content=InputTextMessageContent(
            message_text=(
                f"🎬 <b>{message_title}</b>\n"
                f"🆔 <code>{sid}</code>\n\n"
                f"{link_text}"
            ),
            parse_mode=ParseMode.HTML,
        ),
    )


# =====================================================
# FALLBACK CARD
# =====================================================


def _build_no_result_banner(
    query: str,
) -> InlineQueryResultArticle:
    """
    Banner ketika inline search tidak menemukan hasil yang relevan.
    STRICT MODE: judul harus match penuh.
    """

    safe_query = safe(query)
    digest = hashlib.md5(safe_query.encode()).hexdigest()[:10]

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    text="📩 Request Judul",
                    url="https://t.me/requestdcstv",
                ),
                InlineKeyboardButton(
                    text="🔍 Cari Manual",
                    switch_inline_query_current_chat=safe_query,
                ),
            ]
        ]
    )

    return InlineQueryResultArticle(
        id=f"no_result_banner_{digest}",
        title="Judul Tidak Ditemukan",
        description=get_bot_mood(),
        thumb_url=DEFAULT_THUMBNAIL_URL,
        input_message_content=InputTextMessageContent(
            message_text=(
                "❌ <b>Judul tidak ditemukan</b>\n\n"
                f"Query:\n<b>{safe_query}</b>\n\n"
                "💡 <b>Tips:</b>\n"
                "• Pastikan judul sesuai persis\n"
                "• Gunakan nama resmi drama\n"
                "• Atau kirim poster resmi 📸"
            ),
            parse_mode=ParseMode.HTML,
        ),
        reply_markup=keyboard,
    )


# =====================================================
# META
# =====================================================

_DESC_MAP: dict[ResultKind, str] = {
    ResultKind.SEARCH: "Hasil pencarian 🔍",
    ResultKind.TRENDING: "Trending 🔥",
    ResultKind.POPULAR: "Populer ⭐",
    ResultKind.RANDOM: "Rekomendasi 🎲",
}

_CACHE_TIME_MAP = {
    ResultKind.TRENDING: 10,
    ResultKind.POPULAR: 10,
    ResultKind.RANDOM: 10,
    ResultKind.SEARCH: 2,
}


def _inline_cache_time(kind: ResultKind) -> int:
    return _CACHE_TIME_MAP.get(kind, 5)
