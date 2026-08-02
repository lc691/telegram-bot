import re

TELEGRAM_USERNAME_RE = re.compile(r"^[a-zA-Z0-9_]{5,}$")


def is_valid_telegram_username(value: str) -> bool:
    if not value:
        return False
    return bool(TELEGRAM_USERNAME_RE.fullmatch(value))
