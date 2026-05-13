# dcst_mbot/usecases/repost/title_extractor.py
from .title_parser import extract_title_from_message


def extract_repost_title(message):
    title_db, title_display = extract_title_from_message(message)
    if not title_db:
        return None

    return {
        "db": title_db,
        "display": title_display,
    }
