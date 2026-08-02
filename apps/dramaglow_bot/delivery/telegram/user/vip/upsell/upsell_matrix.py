from typing import Final

UPSELL_MATRIX: Final[dict[str, list[str]]] = {
    # Funnel rule:
    # - Upsell hanya ke paket lebih besar
    # - Urutan list = prioritas (yang ditawarkan dulu)
    # - Builder membatasi max 1 upsell

    "1hari": ["7hari", "30hari"],

    "3hari": ["7hari", "10hari"],

    "7hari": ["10hari", "15hari"],

    "10hari": ["15hari", "30hari"],

    "15hari": ["30hari"],
}


def get_upsell_targets(paket: str) -> list[str]:
    """
    Ambil daftar paket tujuan upsell berdasarkan paket awal.
    Selalu return list baru (aman dimodifikasi caller).
    """
    key = paket.lower().strip()
    return UPSELL_MATRIX.get(key, []).copy()
