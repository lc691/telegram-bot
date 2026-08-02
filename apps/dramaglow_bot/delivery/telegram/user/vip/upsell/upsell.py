from .upsell_builder import UpsellOffer
from .upsell_matrix import get_upsell_targets
from .upsell_copy import UPSELL_COPY


def build_upsell(paket: str, max_offer: int = 1) -> list[UpsellOffer]:
    """
    Bangun daftar upsell offer untuk paket tertentu.
    Maksimal `max_offer` per sesi (default: 1).
    """
    offers: list[UpsellOffer] = []

    base = paket.lower().strip()

    for target in get_upsell_targets(base):
        key = (base, target)

        message = UPSELL_COPY.get(key)
        if not message:
            continue

        offers.append(
            UpsellOffer(
                target_paket=target,
                message=message,
            )
        )

        if len(offers) >= max_offer:
            break

    return offers
