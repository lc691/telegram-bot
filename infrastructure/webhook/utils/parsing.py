# =====================[ UTILITAS PARSING & VALIDASI ]=====================
from configs.logging_setup import log


def parse_payload(req):
    try:
        data = req.get_json(force=True)
        log.info(f"[TRAKTEER] Payload masuk: {data}")
        return data
    except Exception as e:
        log.warning(f"[TRAKTEER] Gagal parse JSON: {e}")
        return None


def extract_message(data: dict) -> str | None:
    try:
        message = data.get("supporter_message")
        if isinstance(message, str):
            return message.strip()
        log.warning(
            "[TRAKTEER] 🟡 Field 'supporter_message' bukan string: %s", type(message)
        )
        return None
    except Exception as e:
        log.error("[TRAKTEER] ❌ Gagal ekstrak supporter_message: %s", e)
        return None
