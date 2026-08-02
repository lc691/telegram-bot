# app/usecases/vip/upsell_matrix.py

from typing import Final

UPSELL_MATRIX: Final[dict[str, list[str]]] = {
    "1hari": ["7hari", "30hari"],
    "3hari": ["7hari", "30hari"],
    "7hari": ["30hari"],
}


def get_upsell_targets(paket: str) -> list[str]:
    """
    Ambil daftar paket tujuan upsell berdasarkan paket awal.
    Urutan list = prioritas upsell.
    """
    return UPSELL_MATRIX.get(paket, []).copy()
