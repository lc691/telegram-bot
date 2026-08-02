# app/usecases/vip/upsell_builder.py
from dataclasses import dataclass


@dataclass(frozen=True)
class UpsellOffer:
    target_paket: str
    message: str
