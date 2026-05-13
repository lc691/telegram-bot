from configs.logging_setup import log
from db.connect import get_dict_cursor

from .repository import extract_part_number


def build_show_cache(show_id: int):
    """
    Build cache daftar file untuk satu show.
    Urut berdasarkan nomor part (domain logic).
    """

    with get_dict_cursor() as (cur, _):
        cur.execute(
            """
            SELECT
                id,
                file_name,
                is_paid
            FROM files
            WHERE show_id = %s
            """,
            (show_id,),
        )
        rows = cur.fetchall()

    if not rows:
        log.warning("[CACHE] no files found show_id=%s", show_id)
        return None

    # ================================
    # SORT (DOMAIN ORDER)
    # ================================
    sorted_files = sorted(
        rows,
        key=lambda r: extract_part_number(r["file_name"]),
    )

    # ================================
    # 🔍 DEBUG: DUMP URUTAN CACHE
    # ================================
    for idx, f in enumerate(sorted_files, start=1):
        key = extract_part_number(f["file_name"])
        log.debug(
            "[CACHE-ORDER] show=%s pos=%s id=%s key=%s paid=%s name='%s'",
            show_id,
            idx,
            f["id"],
            key,
            f["is_paid"],
            f["file_name"],
        )

    ids = [r["id"] for r in sorted_files]

    log.debug(
        "[CACHE-SUMMARY] show=%s total=%s ids=%s",
        show_id,
        len(ids),
        ids,
    )

    return {
        "show_id": show_id,
        "files": sorted_files,
        "ids": ids,
    }


def get_navigation_info_cached(
    show_id: int,
    current_file_id: int,
    *,
    is_vip: bool,
    cache=None,
):
    """
    Navigation resolver (UI-AWARE, POLICY-CONSISTENT).

    Rules:
    - VIP/Admin → boleh navigasi ke semua file
    - FREE user → hanya ke file is_paid = False
    """

    if cache is None:
        cache = build_show_cache(show_id)

    if not cache:
        return None

    if cache.get("show_id") != show_id:
        log.critical(
            "[NAV] CACHE SHOW MISMATCH expected=%s got=%s ids=%s",
            show_id,
            cache.get("show_id"),
            cache.get("ids"),
        )
        return None

    ids = cache["ids"]
    files = cache["files"]

    try:
        idx = ids.index(current_file_id)
    except ValueError:
        log.warning(
            "[NAV] file not found in cache show_id=%s file_id=%s",
            show_id,
            current_file_id,
        )
        return None

    total = len(ids)

    def is_accessible(file: dict) -> bool:
        return is_vip or not file["is_paid"]

    prev_id = None
    for i in range(idx - 1, -1, -1):
        if is_accessible(files[i]):
            prev_id = ids[i]
            break

    next_id = None
    for i in range(idx + 1, total):
        if is_accessible(files[i]):
            next_id = ids[i]
            break

    return {
        "files": files,
        "ids": ids,
        "position": idx + 1,
        "total": total,
        "prev_id": prev_id,
        "next_id": next_id,
        "current_file": files[idx],
        "is_last": next_id is None,
    }
