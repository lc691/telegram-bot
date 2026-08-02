import shlex
from dataclasses import dataclass


@dataclass
class VoucherCommand:
    amount: int
    duration_days: int
    title: str
    content: str


def parse_voucher_command(text: str) -> VoucherCommand | None:
    parts = shlex.split(text)
    if len(parts) != 5:
        return None

    _, amount, duration, title, content = parts

    return VoucherCommand(
        amount=int(amount),
        duration_days=int(duration),
        title=title,
        content=content,
    )
