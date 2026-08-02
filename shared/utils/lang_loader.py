from shared.texts import lang_ms
from shared.texts import lang_en, lang_id

LANG_MAP = {
    "id": lang_id.vip_status,
    "ms": lang_ms.vip_status,
    "en": lang_en.vip_status,
}


def get_texts(lang_code: str = "id") -> dict:
    return LANG_MAP.get(lang_code, lang_id.vip_status)
