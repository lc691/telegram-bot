import os

RUNTIME_MODE = os.getenv("RUNTIME_MODE", "polling").lower()


def is_webhook() -> bool:
    return RUNTIME_MODE == "webhook"


def is_polling() -> bool:
    return RUNTIME_MODE == "polling"
