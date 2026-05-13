# config.py
import os
import logging
from typing import List, Tuple
from dotenv import load_dotenv

# =====================
# ENV LOADING
# =====================
load_dotenv()

# =====================
# LOGGING (SAFE FOR VPS)
# =====================
from configs.logging_setup import log


# =====================
# HELPERS
# =====================
def require_env(name: str, cast=str):
    value = os.getenv(name)
    if value is None or value == "":
        raise RuntimeError(f"ENV '{name}' is required")
    try:
        return cast(value)
    except Exception:
        raise RuntimeError(f"ENV '{name}' must be {cast.__name__}")


def optional_env(name: str, default=None, cast=str):
    value = os.getenv(name)
    if value is None or value == "":
        return default
    try:
        return cast(value)
    except Exception:
        log.warning("ENV %s invalid, fallback to default", name)
        return default


def parse_int_list(raw: str) -> List[int]:
    if not raw:
        return []
    return [int(x) for x in raw.split(",") if x.strip().isdigit()]


def parse_str_list(raw: str) -> List[str]:
    if not raw:
        return []
    return [item.strip() for item in raw.split(",") if item.strip()]


# =====================
# MODE
# =====================
MODE = optional_env("MODE", "production")
IS_DEV = MODE == "development"


# =====================
# TELEGRAM CORE (WAJIB)
# =====================
API_ID = require_env("API_ID", int)
API_HASH = require_env("API_HASH")


# =====================
# BOT LAMA (HACK)
# =====================
BOT_TOKEN = optional_env("BOT_TOKEN_DEV") if IS_DEV else require_env("BOT_TOKEN")
BOT_USERNAME = optional_env("BOT_USERNAME", "drac1n_bot")
BOT_TOKEN_KELOLA = optional_env("BOT_TOKEN_KELOLA")

# =====================
# MULTI BOT TOKEN
# =====================
BOT_TOKEN_GLOW = optional_env("BOT_TOKEN_GLOW")
BOT_TOKEN_UTBK = optional_env("BOT_TOKEN_UTBK")
BOT_TOKEN_CARI = optional_env("BOT_TOKEN_CARI")


# =====================
# DATABASE (WAJIB)
# =====================
PGDATABASE = require_env("PGDATABASE")
PGUSER = require_env("PGUSER")
PGPASSWORD = require_env("PGPASSWORD")
PGHOST = optional_env("PGHOST", "127.0.0.1")
PGPORT = optional_env("PGPORT", 5432, int)


# =====================
# CHANNEL / GROUP
# =====================
DB_DRAMA = optional_env("DB_DRAMA", 0, int)
DB_DRAMA_GLOW = optional_env("DB_DRAMA_GLOW", 0, int)
POSTING_TEST = optional_env("POSTING_TEST", 0, int)
POSTING_CHANNEL = optional_env("POSTING_CHANNEL", 0, int)
GROUP_DISKUSI = optional_env("GROUP_DISKUSI", 0, int)

BACKUP_CHANNEL = parse_str_list(optional_env("BACKUP_CHANNEL", ""))

# =====================
# CHANNEL / GROUP
# =====================
DRAMAGLOW = optional_env("DRAMAGLOW", "@dramaglow")
DRAMAGLOW_GROUP = optional_env("DRAMAGLOW_GROUP", 0, int)

DRAMAMINT = optional_env("DRAMAMINT", "@DramaMint")
DRAMAMINT_GROUP = optional_env("DRAMAMINT_GROUP", 0, int)

POSTING_UTAMA = optional_env("POSTING_UTAMA", 0, int)

# =====================
# ADMIN
# =====================
ADMIN_IDS = parse_int_list(optional_env("ADMIN_IDS", ""))


# =====================
# LIMIT & VIP
# =====================
DAILY_FREE_LIMIT = optional_env("DAILY_FREE_LIMIT", 5, int)
UNLIMITED = optional_env("UNLIMITED", 999999, int)


# =====================
# PAYMENT / TRAKTEER
# =====================
TRAKTEER_SECRET_KEY = optional_env("TRAKTEER_SECRET_KEY")
MANUAL_TRX_TOKEN = optional_env("MANUAL_TRX_TOKEN")


# =====================
# SMTP
# =====================
SMTP_USER = optional_env("SMTP_USER")
SMTP_PASS = optional_env("SMTP_PASS")


# =====================
# CRON / WORKER
# =====================
CLEANUP_INTERVAL = optional_env("CLEANUP_INTERVAL", 600, int)
UPLOAD_DELAY = optional_env("UPLOAD_DELAY", 1.5, float)


# =====================
# STATIC CONFIG
# =====================
TARGET_CHANNELS = [
    "listdramaglow",
    "netshortx",
    "dramawavex",
    "flickreelss",
    "dramaboxzz",
    "reelshorttz",
    "stardusttvv",
    "shortmaxtvv",
    "goodshortx",
    "bilitvv",
    "iqiyis",
    "melolox",
    "reelbuzt",
    "flextvv",
    "viglooo",
    "dramabitex",
    "flarefloww",
    "idramas",
    "moboreelsx",
    "rapidtvv",
    "cubetvx",
    "veloloxx",
    "dramanova",
]

SOURCE_CHANNEL_MAP = {
    "dramabox": ["dramaboxzz", "listdramaglow"],
    "flickreels": ["flickreelss", "listdramaglow"],
    "netshort": ["netshortx", "listdramaglow"],
    "dramawave": ["dramawavex", "listdramaglow"],
    "reelshort": ["reelshorttz", "listdramaglow"],
    "stardusttv": ["stardusttvv", "listdramaglow"],
    "shortmax": ["shortmaxtvv", "listdramaglow"],
    "goodshort": ["goodshortx", "listdramaglow"],
    "bilitv": ["bilitvv", "listdramaglow"],
    "iqiyi": ["iqiyis", "listdramaglow"],
    "melolo": ["melolox", "listdramaglow"],
    "reelbuzz": ["reelbuzt", "listdramaglow"],
    "flextv": ["flextvv", "listdramaglow"],
    "vigloo": ["viglooo", "listdramaglow"],
    "dramabite": ["dramabitex", "listdramaglow"],
    "flareflow": ["flarefloww", "listdramaglow"],
    "idrama": ["idramas", "listdramaglow"],
    "moboreels": ["moboreelsx", "listdramaglow"],
    "rapidtv": ["rapidtvv", "listdramaglow"],
    "cubetv": ["cubetvx", "listdramaglow"],
    "velolo": ["veloloxx", "listdramaglow"],
    "dramanova": ["dramanovax", "listdramaglow"],
}

REQUIRED_CHANNELS: List[Tuple[str, str]] = [
    ("dracinshort", "https://t.me/dracinshort"),
    ("dramaglow", "https://t.me/dramaglow"),
    ("dramacinavip", "https://t.me/dramacinavip"),
    # ("dracinshortgroup", "https://t.me/dracinshortgroup"),
]

REQUEST_CHANNELS: List[Tuple[str, str]] = [
    ("requestdcstv", "https://t.me/requestdcstv"),
]

REQUIRED_CHANNELS_UTBK: List[Tuple[str, str]] = [
    ("dcstutbk2025", "https://t.me/dcstutbk2025"),
]


# =====================
# SESSION (FOR WORKER / CRON)
# =====================
BOT_SESSION = {
    "name": "vip-bot-cron",
    "api_id": API_ID,
    "api_hash": API_HASH,
    "bot_token": BOT_TOKEN,
}


USER_SESSION = {
    "name": "user-session",
    "api_id": API_ID,
    "api_hash": API_HASH,
}

# =====================
# SPECIAL DONORS (OPTIONAL)
# =====================
SPECIAL_DONORS = set()

DEFAULT_THUMBNAIL_FILE_ID = optional_env("DEFAULT_THUMBNAIL_FILE_ID")
DEFAULT_THUMBNAIL_URL = optional_env("DEFAULT_THUMBNAIL_URL")
VIP_UPGRADE_URL = optional_env("VIP_UPGRADE_URL")

# =====================
# DEBUG SUMMARY (LOG SAFE)
# =====================
log.info("Running in %s mode", MODE.upper())
log.info("Bot: %s", BOT_USERNAME)
log.info("DB: %s@%s:%s/%s", PGUSER, PGHOST, PGPORT, PGDATABASE)
log.info("Admins: %s", ADMIN_IDS)
