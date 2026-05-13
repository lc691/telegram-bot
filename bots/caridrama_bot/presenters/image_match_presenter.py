import html
from typing import Optional

from ..common.ui.smart_keyboard import build_keyboard
from ..usecases.image_match.types import MatchResult, MatchStatus


def _fmt(val: Optional[float]) -> str:
    return f"{val:.3f}" if isinstance(val, (int, float)) else "-"


def _safe_title(best: dict | None) -> str:
    title = (best or {}).get("title")
    if not title:
        return "Judul belum tersedia"
    return html.escape(title)


def _fmt_id(best: dict | None) -> str | None:
    sid = (best or {}).get("id")
    return f"🆔 <b>ID:</b> <code>{sid}</code>" if sid else None


class ImageMatchPresenter:
    """
    Presenter khusus Image Match.
    Tugas: MatchResult -> UI payload Telegram
    """

    # ==================================================
    # PUBLIC ENTRYPOINT
    # ==================================================
    @staticmethod
    def build(result: MatchResult, user_id: int) -> dict:
        status = result.status

        if status == MatchStatus.CONFIDENT:
            return ImageMatchPresenter.confident(result)

        if status == MatchStatus.AMBIGUOUS:
            return ImageMatchPresenter.ambiguous(result, user_id)

        if status == MatchStatus.NO_FILE:
            return ImageMatchPresenter.no_file(result, user_id)

        return ImageMatchPresenter.no_match(result, user_id)

    # ==================================================
    # CONFIDENT
    # ==================================================
    @staticmethod
    def confident(result: MatchResult) -> dict:
        best = result.best or {}
        title = _safe_title(best)
        sid_line = _fmt_id(best)

        lines = [
            f"🎬 <b>{title}</b>",
        ]

        if sid_line:
            lines.append(sid_line)

        lines.append(f"📊 <b>Similarity:<b> {_fmt(best.get('similarity'))}")

        if result.url:
            lines.insert(1, f"🔗 {result.url}")
        else:
            lines.insert(1, "📂 <b>File belum tersedia</b>")

        payload = {"text": "\n".join(lines)}
        thumb = best.get("thumbnail_url")
        if thumb:
            payload["thumb_url"] = thumb
        return payload

    # ==================================================
    # AMBIGUOUS (OCR SUDAH MASUK DI MESSAGE)
    # ==================================================
    @staticmethod
    def ambiguous(result: MatchResult, user_id: int) -> dict:
        best = result.best or {}
        title = _safe_title(best)
        sid = best.get("id")
        id_line = f"🆔 <b>ID:</b> <code>{sid}</code>\n" if sid else ""

        caption = (
            f"🤔 <b>Apakah ini yang kamu maksud?</b>\n\n"
            f"<b>{title}</b>\n"
            f"{id_line}"
            f"📊 <b>Similarity:</b> {_fmt(best.get('similarity'))}\n"
            f"📊 <b>Gap:</b> {_fmt(result.gap)}\n\n"
            f"{result.message or '<b>Kalau bukan, kamu bisa cari manual</b> 👇'}"
        )

        payload = {
            "caption": caption,
            "reply_markup": build_keyboard(
                search_query=title if title != "Judul belum tersedia" else "",
                confirm_id=best.get("id"),
                user_id=user_id,
            ),
        }

        # 🛡️ PHOTO OPSIONAL
        thumb = best.get("thumbnail_url")
        if thumb:
            payload["photo"] = thumb
        else:
            payload["text"] = caption

        return payload

    # ==================================================
    # NO_FILE
    # ==================================================
    @staticmethod
    def no_file(result: MatchResult, user_id: int) -> dict:
        best = result.best or {}

        title = _safe_title(best)
        sid = best.get("id")
        thumbnail_url = best.get("thumbnail_url")

        id_line = f"🆔 <b>ID:</b> <code>{sid}</code>\n" if sid else ""

        return {
            "thumb_url": thumbnail_url,
            "text": (
                f"🎬 <b>{title}</b>\n"
                f"{id_line}"
                f"📂 <b>File belum tersedia.</b>\n\n"
                f"<b>Kamu bisa minta admin</b> 👇"
            ),
            "reply_markup": build_keyboard(
                allow_request=True,
                show_id=sid,
                user_id=user_id,
            ),
        }

    # ==================================================
    # NO_MATCH
    # ==================================================
    @staticmethod
    def no_match(result: MatchResult, user_id: int) -> dict:
        return {
            "text": result.message,
            "reply_markup": build_keyboard(
                search_query="",
                user_id=user_id,
            ),
        }
