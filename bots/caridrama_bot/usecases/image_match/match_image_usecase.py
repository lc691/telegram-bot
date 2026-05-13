import os
import asyncio
from typing import List, Dict

from configs.logging_setup import log

from .match_threshold_service import get_match_thresholds
from .types import MatchResult, MatchStatus

from ...domain.show_repository import get_show_with_latest_file_full, get_show_by_id
from ...utils.image_utils import load_image_resized
from ...services.image_match_client import match_image_via_vps
from ..request.save_show_request import (
    save_show_request_for_unknown,
)
from ...utils.mood_bot import get_bot_mood


# ======================================================
# Helpers (SAFE & LOCAL)
# ======================================================
def rerank_with_ocr(results: List[Dict], ocr_text: str | None) -> List[Dict]:
    """
    OCR hanya untuk ordering (tidak mempengaruhi threshold).
    """
    if not ocr_text:
        return results

    ocr_text = ocr_text.lower()

    def score(r: Dict) -> float:
        base = float(r.get("similarity", 0.0))
        title = (r.get("title") or "").lower()
        if title and title in ocr_text:
            return base + 0.05  # bonus kecil, aman
        return base

    return sorted(results, key=score, reverse=True)


def choose_best_candidate(results: List[Dict]) -> Dict:
    """
    Pilih kandidat paling aman:
    1) ada show_id
    2) fallback similarity tertinggi
    """
    for r in results:
        if r.get("show_id"):
            return r
    return results[0]


# ======================================================
# MAIN USECASE
# ======================================================
async def match_image_usecase(
    *,
    user_id: int,
    image_path: str,
) -> MatchResult:

    log.info(
        "[MATCH] START user=%s image=%s",
        user_id,
        os.path.basename(image_path) if image_path else "-",
    )

    # --------------------------------------------------
    # 1️⃣ VALIDASI FILE
    # --------------------------------------------------
    if not image_path or not os.path.exists(image_path):
        return MatchResult(
            status=MatchStatus.NO_MATCH,
            message="File gambar tidak valid.",
        )

    img = load_image_resized(image_path)
    if img is None:
        return MatchResult(
            status=MatchStatus.NO_MATCH,
            message="Gambar tidak dapat diproses.",
        )
    del img  # RAM hygiene

    # --------------------------------------------------
    # 2️⃣ FAISS SEARCH VIA VPS
    # --------------------------------------------------
    try:
        raw = await asyncio.to_thread(
            match_image_via_vps,
            image_path,
        )
        ocr_text = raw.get("ocr_text")
        results = raw.get("results", [])
    except Exception:
        log.exception("[MATCH] VPS image-match failed")
        return MatchResult(
            status=MatchStatus.NO_MATCH,
            message="Gagal memproses gambar.",
        )

    if not results:
        return MatchResult(
            status=MatchStatus.NO_MATCH,
            message="Tidak ada judul yang cocok.",
        )

    # --------------------------------------------------
    # 3️⃣ SIMPAN FAISS SCORE ASLI (UNTUK THRESHOLD)
    # --------------------------------------------------
    faiss_results = results[:]

    best_sim = float(faiss_results[0].get("similarity", 0.0))
    second_sim = (
        float(faiss_results[1].get("similarity", 0.0))
        if len(faiss_results) > 1
        else 0.0
    )
    gap = best_sim - second_sim

    # --------------------------------------------------
    # 4️⃣ LOAD THRESHOLD
    # --------------------------------------------------
    thresholds = get_match_thresholds()
    CONFIDENT_THRESHOLD = thresholds["confident_threshold"]
    MIN_ACCEPT_THRESHOLD = thresholds["min_accept_threshold"]
    AMBIGUITY_GAP = thresholds["ambiguity_gap"]

    log.info(
        "[MATCH_THRESHOLDS] conf=%.3f min=%.3f gap=%.3f",
        CONFIDENT_THRESHOLD,
        MIN_ACCEPT_THRESHOLD,
        AMBIGUITY_GAP,
    )

    log.info(
        "[MATCH_DEBUG] best=%.6f second=%.6f gap=%.6f | "
        "thresholds(conf=%.6f min=%.6f gap=%.6f)",
        best_sim,
        second_sim,
        gap,
        CONFIDENT_THRESHOLD,
        MIN_ACCEPT_THRESHOLD,
        AMBIGUITY_GAP,
    )

    # --------------------------------------------------
    # 5️⃣ TENTUKAN STATUS (HARD RULE, SEKALI SAJA)
    # --------------------------------------------------
    # if gap < AMBIGUITY_GAP:
    #     status = MatchStatus.AMBIGUOUS
    # elif best_sim >= CONFIDENT_THRESHOLD:
    #     status = MatchStatus.CONFIDENT
    # elif best_sim >= MIN_ACCEPT_THRESHOLD:
    #     status = MatchStatus.AMBIGUOUS
    # else:
    #     status = MatchStatus.NO_MATCH

    if best_sim >= CONFIDENT_THRESHOLD and gap >= AMBIGUITY_GAP:
        status = MatchStatus.CONFIDENT
    elif best_sim >= MIN_ACCEPT_THRESHOLD:
        status = MatchStatus.AMBIGUOUS
    else:
        status = MatchStatus.NO_MATCH

    # --------------------------------------------------
    # 6️⃣ OCR RERANK (SETELAH STATUS DIPUTUSKAN)
    # --------------------------------------------------
    results = rerank_with_ocr(results, ocr_text)
    raw_best = choose_best_candidate(results)

    best = {
        "id": raw_best.get("show_id"),
        "thumbnail_url": raw_best.get("thumbnail_url"),
        "similarity": float(raw_best.get("similarity", best_sim)),
        "title": raw_best.get("title") or "Judul mirip ditemukan",
    }

    show_meta = None
    # --------------------------------------------------
    # 7️⃣ FETCH METADATA DARI DB (JIKA PERLU)
    # --------------------------------------------------
    if best.get("id") and not raw_best.get("title"):
        show_meta = await asyncio.to_thread(
            get_show_by_id,
            best["id"],
        )
        if show_meta:
            best["title"] = show_meta["title"]
            best["thumbnail_url"] = show_meta.get("thumbnail_url")

    # --------------------------------------------------
    # 8️⃣ NO MATCH
    # --------------------------------------------------

    if status == MatchStatus.NO_MATCH:
        return MatchResult(
            status=MatchStatus.NO_MATCH,
            message=f"{get_bot_mood()}\n👇 <b>Silakan bisa cari manual</b>",
        )

    # --------------------------------------------------
    # 9️⃣ CONFIDENT
    # --------------------------------------------------
    if status == MatchStatus.CONFIDENT:

        show_meta = await asyncio.to_thread(
            get_show_by_id,
            best["id"],
        )

        if not show_meta:
            return MatchResult(
                status=MatchStatus.NO_MATCH,
                message="Judul tidak ditemukan di database.",
            )

        best["title"] = show_meta["title"]
        best["thumbnail_url"] = show_meta.get("thumbnail_url")

        show_file = await asyncio.to_thread(
            get_show_with_latest_file_full,
            best["id"],
        )

        if not show_file:
            return MatchResult.from_best(
                status=MatchStatus.NO_FILE,
                best=best,
                message="Judul ditemukan, tetapi file belum tersedia.",
            )

        channel = show_file["channel_username"]
        msg_id = show_file["file_message_id"]

        url = (
            f"https://t.me/c/{channel[4:]}/{msg_id}"
            if channel.startswith("-100")
            else f"https://t.me/{channel}/{msg_id}"
        )

        return MatchResult.from_best(
            status=MatchStatus.CONFIDENT,
            best=best,
            gap=gap,
            url=url,
            message="Judul ditemukan.",
        )

    # --------------------------------------------------
    # 🔟 AMBIGUOUS
    # --------------------------------------------------
    known_candidate = bool(best.get("id"))

    if known_candidate:
        return MatchResult.from_best(
            status=MatchStatus.AMBIGUOUS,
            best=best,
            gap=gap,
            message=(
                f"⚠️ <b>Kemiripan belum meyakinkan</b>\n\n"
                f"📌 <b>Kandidat terdekat:</b>\n"
                f"👉 <b>{best['title']}</b>\n"
                f"📊 <b>Selisih skor:</b> {gap:.4f}\n\n"
                f"<b>Silakan konfirmasi atau cari manual.</b>👇"
            ),
        )

    await asyncio.to_thread(
        save_show_request_for_unknown,
        user_id=user_id,
        image_path=image_path,
    )

    return MatchResult.from_best(
        status=MatchStatus.AMBIGUOUS,
        best=best,
        gap=gap,
        message="🤔 Judul mirip ditemukan, tapi belum ada di database.",
    )
