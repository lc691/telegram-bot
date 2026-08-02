from datetime import datetime
from zoneinfo import ZoneInfo


def get_greeting_by_country(country_code: str) -> str:
    timezone_map = {
        "ID": ZoneInfo("Asia/Jakarta"),
        "MY": ZoneInfo("Asia/Kuala_Lumpur"),
    }
    tz = timezone_map.get(country_code.upper(), ZoneInfo("Asia/Jakarta"))
    hour = datetime.now(tz).hour

    if 5 <= hour < 12:
        return "Selamat pagi"
    elif 12 <= hour < 17:
        return "Selamat siang"
    elif 17 <= hour < 21:
        return "Selamat sore"
    else:
        return "Selamat malam"


def get_country_code_by_language(language_code: str) -> str:
    lang_to_country = {
        "id": "ID",  # Indonesia
        "ms": "MY",  # Malaysia
    }
    return lang_to_country.get(language_code, "ID")  # Default Indonesia
