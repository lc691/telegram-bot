import logging
import os
import sys
import re

from datetime import datetime
from logging.handlers import TimedRotatingFileHandler
from pytz import timezone

from colorama import Fore, Style, init as colorama_init
from .trace import get_trace_id

colorama_init(autoreset=True)

JAKARTA_TZ = timezone("Asia/Jakarta")
LOGGER_NAME = "drac1n"

# ======================================================
# Filters
# ======================================================


class TraceIdFilter(logging.Filter):
    def filter(self, record):
        record.trace_id = get_trace_id() or "-"
        return True


class UserFlowSeparatorFilter(logging.Filter):
    """
    Tampilkan visual separator block saat:
    - log adalah [START]
    - user_id berbeda dari START sebelumnya
    """

    _START_RE = re.compile(r"\[START\].*user=(\d+)")

    SEPARATOR = "=" * 20 + " USER FLOW " + "=" * 20

    def __init__(self):
        super().__init__()
        self._last_user_id = None

    def filter(self, record: logging.LogRecord) -> bool:
        message = record.getMessage()

        m = self._START_RE.search(message)
        if not m:
            return True

        user_id = m.group(1)

        if self._last_user_id and user_id != self._last_user_id:
            record.msg = f"\n{self.SEPARATOR}\n{message}"
            record.args = ()

        self._last_user_id = user_id
        return True


# ======================================================
# Formatters
# ======================================================


class JakartaFormatter(logging.Formatter):
    def formatTime(self, record, datefmt=None):
        dt = datetime.fromtimestamp(record.created, tz=JAKARTA_TZ)
        if datefmt:
            return dt.strftime(datefmt)
        return dt.isoformat()


class ColoredFormatter(JakartaFormatter):
    COLORS = {
        logging.DEBUG: Fore.CYAN,
        logging.INFO: Fore.GREEN,
        logging.WARNING: Fore.YELLOW,
        logging.ERROR: Fore.RED,
        logging.CRITICAL: Fore.MAGENTA,
    }

    def format(self, record):
        original_levelname = record.levelname
        color = self.COLORS.get(record.levelno, "")
        record.levelname = f"{color}{original_levelname}{Style.RESET_ALL}"
        try:
            return super().format(record)
        finally:
            record.levelname = original_levelname


# ======================================================
# Setup
# ======================================================


def setup_logger(log_dir: str = "logs", level: int = logging.INFO) -> logging.Logger:
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "bot.log")

    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(level)
    logger.propagate = False

    if logger.handlers:
        logger.handlers.clear()

    # ==================================================
    # Filters
    # ==================================================
    trace_filter = TraceIdFilter()
    flow_filter = UserFlowSeparatorFilter()

    # ==================================================
    # File handler
    # ==================================================
    file_handler = TimedRotatingFileHandler(
        filename=log_file,
        when="midnight",
        interval=1,
        backupCount=7,
        encoding="utf-8",
        utc=False,
    )
    file_handler.setFormatter(
        JakartaFormatter(
            "[%(asctime)s] [%(levelname)s] [%(trace_id)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )

    file_handler.addFilter(trace_filter)
    file_handler.addFilter(flow_filter)

    logger.addHandler(file_handler)

    # ==================================================
    # Console handler
    # ==================================================
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(
        ColoredFormatter(
            "[%(levelname)s] [%(trace_id)s] %(message)s",
        )
        # ColoredFormatter(
        #     "[%(asctime)s] [%(levelname)s] [%(trace_id)s] %(message)s",
        #     datefmt="%H:%M:%S",
        # )
    )

    console_handler.addFilter(trace_filter)
    console_handler.addFilter(flow_filter)

    logger.addHandler(console_handler)

    # ==================================================
    # Silence noisy loggers
    # ==================================================
    for noisy in (
        "pyrogram",
        "apscheduler",
        "httpx",
        "uvicorn.access",
        "uvicorn.error",
        "fastapi",
    ):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    return logger


# ======================================================
# Public logger reference
# ======================================================

log = logging.getLogger(LOGGER_NAME)

