from config import SOURCE_CHANNEL_MAP


def resolve_target_channels(source_label: str) -> list[str]:
    if not source_label:
        return []

    normalized = source_label.strip().lower()
    return SOURCE_CHANNEL_MAP.get(normalized, [])

