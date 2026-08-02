from configs.logging_setup import log
from database.connection import get_dict_cursor


DEFAULT_THRESHOLDS = {
    "confident_threshold": 0.85,
    "min_accept_threshold": 0.78,
    "ambiguity_gap": 0.03,
}


def load_match_thresholds() -> dict:
    """
    Load threshold dari DB.
    FAIL-SAFE: fallback ke default kalau DB error / data tidak lengkap.
    """
    thresholds = DEFAULT_THRESHOLDS.copy()

    try:
        with get_dict_cursor() as (cur, _):
            cur.execute(
                """
                SELECT key, value
                FROM match_thresholds
                WHERE key IN (
                    'confident_threshold',
                    'min_accept_threshold',
                    'ambiguity_gap'
                )
                """
            )

            for row in cur.fetchall():
                thresholds[row["key"]] = float(row["value"])

    except Exception:
        log.exception("[THRESHOLD] Failed load from DB, using defaults")

    return thresholds
