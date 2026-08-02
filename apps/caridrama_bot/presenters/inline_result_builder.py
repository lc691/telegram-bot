import asyncio
import hashlib
import json
import re
import time

from collections import defaultdict, deque
from datetime import datetime
from html import escape
from urllib.parse import (
    parse_qs,
    unquote,
    urlparse,
)

from pyrogram.enums import ParseMode
from pyrogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InlineQueryResultArticle,
    InputTextMessageContent,
)

from configs.logging_setup import log

from ..config.settings import DEFAULT_THUMBNAIL_URL
from ..usecases.inline_search.types import (
    ResultKind,
    SearchResult,
    ShowRow,
)

from ..utils.mood_bot import get_bot_mood
from ..utils.text_highlight import (
    highlight_query_adaptive,
    safe,
)

# =========================================================
# CONFIG
# =========================================================

BLOCKED_DOMAINS = {
    "core.mebilu.com",
}

ALLOWED_IMAGE_EXT = (
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
)

SUSPICIOUS_URL_PATTERNS = [
    r"bit\.ly\/",
    r"tinyurl\.com\/",
    r"click\.me\/",
    r"join\.me\/",
    r"xn--",
]

_CACHE_TIME_MAP = {
    ResultKind.TRENDING: 10,
    ResultKind.POPULAR: 10,
    ResultKind.RANDOM: 10,
    ResultKind.SEARCH: 2,
}

_DESC_MAP = {
    ResultKind.SEARCH: "Hasil pencarian 🔍",
    ResultKind.TRENDING: "Trending 🔥",
    ResultKind.POPULAR: "Populer ⭐",
    ResultKind.RANDOM: "Rekomendasi 🎲",
}

MAX_HISTORY = 1000
MAX_TIMING_PER_CARD = 20

# =========================================================
# METRICS
# =========================================================

class MetricsCollector:

    def __init__(self):

        self.timings = defaultdict(
            lambda: deque(maxlen=MAX_TIMING_PER_CARD)
        )

        self.duplicate_thumbs = defaultdict(set)

        self.slow_cards = deque(
            maxlen=MAX_HISTORY
        )

    def record_card_build(
        self,
        card_id: str,
        duration_ms: float,
    ):

        self.timings[card_id].append(duration_ms)

        if duration_ms > 500:

            self.slow_cards.append(
                {
                    "card_id": card_id,
                    "duration_ms": round(duration_ms, 2),
                    "timestamp": datetime.now().isoformat(),
                }
            )

    def record_thumb_usage(
        self,
        thumb_url: str,
        show_id: int,
    ):
        self.duplicate_thumbs[thumb_url].add(show_id)

    def get_thumb_duplicate_count(
        self,
        thumb_url: str,
    ) -> int:

        return len(
            self.duplicate_thumbs.get(
                thumb_url,
                set(),
            )
        )

    def get_metrics_snapshot(self):

        all_timings = []

        for timings in self.timings.values():
            all_timings.extend(timings)

        avg_ms = (
            sum(all_timings) / len(all_timings)
            if all_timings
            else 0
        )

        duplicate_count = sum(
            1
            for shows in self.duplicate_thumbs.values()
            if len(shows) > 1
        )

        return {
            "avg_build_ms": round(avg_ms, 2),
            "slow_cards": len(self.slow_cards),
            "duplicate_thumbs": duplicate_count,
            "unique_thumbs": len(self.duplicate_thumbs),
        }

    def export_light_telemetry(self):

        return json.dumps(
            {
                "timestamp": datetime.now().isoformat(),
                "metrics": self.get_metrics_snapshot(),
            },
            indent=2,
        )


_metrics = MetricsCollector()

# =========================================================
# DUPLICATE DETECTOR
# =========================================================

class DuplicateThumbDetector:

    def __init__(self):

        self.thumb_hash_map = defaultdict(
            lambda: deque(maxlen=100)
        )

    def add_thumbnail(
        self,
        thumb_url: str,
        show_id: int,
    ) -> bool:

        if not thumb_url:
            return False

        thumb_hash = hashlib.md5(
            thumb_url.encode()
        ).hexdigest()

        shows = self.thumb_hash_map[thumb_hash]

        if show_id not in shows:
            shows.append(show_id)

        return len(shows) > 1

    def get_duplicate_count(
        self,
        thumb_url: str,
    ) -> int:

        if not thumb_url:
            return 0

        thumb_hash = hashlib.md5(
            thumb_url.encode()
        ).hexdigest()

        return max(
            0,
            len(self.thumb_hash_map[thumb_hash]) - 1,
        )


_dup_detector = DuplicateThumbDetector()

# =========================================================
# SLOW DETECTOR
# =========================================================

class SlowCardDetector:

    def __init__(
        self,
        threshold_ms: int = 500,
    ):

        self.threshold = threshold_ms

        self.history = deque(
            maxlen=MAX_HISTORY
        )

    def record(
        self,
        card_id: str,
        build_time_ms: float,
    ) -> bool:

        if build_time_ms <= self.threshold:
            return False

        self.history.append(
            {
                "card_id": card_id,
                "build_ms": round(build_time_ms, 2),
                "timestamp": datetime.now().isoformat(),
            }
        )

        return True

    def recent(
        self,
        limit: int = 10,
    ):

        return list(self.history)[-limit:]


_slow_detector = SlowCardDetector()

# =========================================================
# URL SECURITY
# =========================================================

def is_suspicious_url(
    url: str,
):

    if not url:
        return False, None

    url_lower = url.lower()

    for pattern in SUSPICIOUS_URL_PATTERNS:

        if re.search(
            pattern,
            url_lower,
            re.IGNORECASE,
        ):
            return True, pattern

    parsed = urlparse(url)

    if re.match(
        r"^\d{1,3}(?:\.\d{1,3}){3}$",
        parsed.netloc,
    ):
        return True, "ip-address"

    return False, None

# =========================================================
# THUMB CLEANER
# =========================================================

def clean_thumb_url(
    url: str | None,
    *,
    sid: int | None = None,
):

    if not url:
        return None

    try:

        raw = url

        url = url.strip()

        url = url.replace(
            "&amp;",
            "&",
        )

        if "," in url:
            url = url.split(",")[0].strip()

        url = re.sub(
            r"\s+\d+w$",
            "",
            url,
        )

        url = url.split(" ")[0]

        url = unquote(url)

        if not url.startswith(
            (
                "http://",
                "https://",
            )
        ):

            log.warning(
                "[INLINE_BAD_THUMB] show=%s invalid_scheme=%r",
                sid,
                raw,
            )

            return None

        parsed = urlparse(url)

        if parsed.netloc in BLOCKED_DOMAINS:

            qs = parse_qs(parsed.query)

            extracted = qs.get("url")

            if extracted:
                url = extracted[0]
                parsed = urlparse(url)

        domain = parsed.netloc.lower()

        if not domain:
            return None

        path = parsed.path.lower()

        has_valid_ext = any(
            ext in path
            for ext in ALLOWED_IMAGE_EXT
        )

        if not has_valid_ext:

            log.debug(
                "[INLINE_THUMB_NO_EXT] show=%s path=%s",
                sid,
                path,
            )

        suspicious, reason = is_suspicious_url(url)

        if suspicious:

            log.warning(
                "[INLINE_SUSPICIOUS_URL] show=%s reason=%s",
                sid,
                reason,
            )

        is_duplicate = _dup_detector.add_thumbnail(
            url,
            sid,
        )

        if is_duplicate:

            log.debug(
                "[INLINE_DUPLICATE_THUMB] show=%s",
                sid,
            )

        return url

    except Exception:

        log.exception(
            "[INLINE_THUMB_EXCEPTION] show=%s",
            sid,
        )

        return None

# =========================================================
# IMAGE CHECKER
# =========================================================

async def check_broken_image(
    url: str,
    timeout: float = 5.0,
):

    import aiohttp

    if not url:
        return True, "empty"

    try:

        async with aiohttp.ClientSession() as session:

            async with session.head(
                url,
                timeout=timeout,
                allow_redirects=True,
            ) as resp:

                if resp.status != 200:
                    return True, f"http_{resp.status}"

                content_type = (
                    resp.headers.get(
                        "content-type",
                        "",
                    ).lower()
                )

                if "image" not in content_type:
                    return True, content_type

                return False, None

    except asyncio.TimeoutError:
        return True, "timeout"

    except Exception as e:
        return True, str(e)

# =========================================================
# INLINE BUILDER
# =========================================================

def build_inline_results(
    *,
    result: SearchResult,
    query: str,
    offset: int,
):

    started = time.perf_counter()

    if result.kind == ResultKind.FALLBACK:
        return [_build_no_result_banner(query)]

    rows = result.rows or []

    results = []

    skipped = 0
    fallback_thumb = 0

    for i, row in enumerate(rows):

        try:

            sid = row[0]

            card_started = time.perf_counter()

            unique_id = hashlib.md5(
                f"{result.kind.value}:{sid}:{offset+i}".encode()
            ).hexdigest()

            card = build_show_card(
                row=row,
                kind=result.kind,
                query=query,
                unique_id=unique_id,
            )

            build_ms = (
                time.perf_counter() - card_started
            ) * 1000

            _metrics.record_card_build(
                unique_id,
                build_ms,
            )

            _slow_detector.record(
                unique_id,
                build_ms,
            )

            if card.thumb_url == DEFAULT_THUMBNAIL_URL:
                fallback_thumb += 1

            results.append(card)

        except Exception:

            skipped += 1

            log.exception(
                "[INLINE_BUILD_ERROR] row=%r",
                row,
            )

    took_ms = round(
        (time.perf_counter() - started) * 1000,
        2,
    )

    log.info(
        "[INLINE_BUILD_DONE] results=%s skipped=%s fallback=%s took=%sms",
        len(results),
        skipped,
        fallback_thumb,
        took_ms,
    )

    return results

# =========================================================
# CARD BUILDER
# =========================================================

def build_show_card(
    *,
    row: ShowRow,
    kind: ResultKind,
    query: str,
    unique_id: str,
):

    started = time.perf_counter()

    sid, title, thumb, channel_username, message_id = row

    safe_title = safe(title)

    thumb = clean_thumb_url(
        thumb,
        sid=sid,
    )

    thumb_url = thumb or DEFAULT_THUMBNAIL_URL

    # =====================================================
    # TELEGRAM LINK
    # =====================================================

    if channel_username and message_id:

        telegram_link = (
            f"https://t.me/"
            f"{channel_username}/"
            f"{message_id}"
        )

    else:

        telegram_link = "📭 File belum tersedia"

    # =====================================================
    # TITLE
    # =====================================================

    if kind == ResultKind.SEARCH and query:

        display_title = highlight_query_adaptive(
            title,
            query,
            device="mobile",
        )

    else:
        display_title = safe_title

    description = (
        f"ID: {sid} | "
        f"{_DESC_MAP.get(kind, 'Drama')}"
    )

    duplicate_count = _dup_detector.get_duplicate_count(
        thumb_url
    )

    if duplicate_count > 0:

        description += f" | 📸 {duplicate_count}"

        _metrics.record_thumb_usage(
            thumb_url,
            sid,
        )

    # =====================================================
    # MESSAGE TEXT
    # =====================================================
    # URL dibikin sendiri + dipisah
    # agar preview Telegram lebih stabil
    # =====================================================

    message_text = (
        f"🎬 <b>{display_title}</b>\n"
        f"🆔 <b>{sid}</b>\n\n"
        f"{telegram_link}"
    )

    result = InlineQueryResultArticle(
        id=unique_id,
        title=display_title,
        description=description,
        thumb_url=thumb_url,
        input_message_content=InputTextMessageContent(
            message_text=message_text,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=False,
        ),
    )

    took_ms = round(
        (time.perf_counter() - started) * 1000,
        2,
    )

    if took_ms > 500:

        log.warning(
            "[INLINE_CARD_SLOW] show=%s took=%sms",
            sid,
            took_ms,
        )

    return result

# =========================================================
# FALLBACK
# =========================================================

def _build_no_result_banner(
    query: str,
):

    safe_query = safe(query)

    digest = hashlib.md5(
        safe_query.encode()
    ).hexdigest()[:10]

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
                f"<b>{safe_query}</b>"
            ),
            parse_mode=ParseMode.HTML,
        ),
        reply_markup=keyboard,
    )

# =========================================================
# CACHE
# =========================================================

def _inline_cache_time(
    kind: ResultKind,
):

    return _CACHE_TIME_MAP.get(
        kind,
        5,
    )

# =========================================================
# EXPORTS
# =========================================================

def get_metrics_report():

    return _metrics.get_metrics_snapshot()

def get_slow_cards_report(
    limit: int = 20,
):

    return _slow_detector.recent(limit)

def get_duplicate_thumbs_report():

    result = {}

    for thumb_hash, shows in _dup_detector.thumb_hash_map.items():

        if len(shows) > 1:
            result[thumb_hash] = list(shows)

    return result