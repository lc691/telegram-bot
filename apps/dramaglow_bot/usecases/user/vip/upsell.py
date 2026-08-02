# app/usecases/vip/upsell_builder.py

from .upsell_builder import UpsellOffer
from ....presenters.user.vip.upsell_copy import UPSELL_COPY
from .upsell_matrix import get_upsell_targets


def build_upsell(paket: str) -> list[UpsellOffer]:
    """
    Bangun daftar upsell offer untuk paket tertentu.
    """
    offers: list[UpsellOffer] = []

    for target in get_upsell_targets(paket):
        message = UPSELL_COPY.get((paket, target))
        if not message:
            continue

        offers.append(
            UpsellOffer(
                target_paket=target,
                message=message,
            )
        )

    return offers
