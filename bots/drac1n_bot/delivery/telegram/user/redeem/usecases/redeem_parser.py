from dataclasses import dataclass


@dataclass
class RedeemInput:
    target_user_id: int
    voucher_code: str
    mode: str  # "user" | "admin"


def parse_redeem_command(
    *,
    text: str,
    sender_id: int,
    is_admin: bool,
) -> RedeemInput | None:
    parts = text.strip().split()

    if len(parts) == 2:
        return RedeemInput(
            target_user_id=sender_id,
            voucher_code=parts[1].upper(),
            mode="user",
        )

    if len(parts) == 3 and is_admin:
        return RedeemInput(
            target_user_id=int(parts[1]),
            voucher_code=parts[2].upper(),
            mode="admin",
        )

    return None
