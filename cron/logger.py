import logging
import sys
from datetime import datetime

from pytz import timezone

from ..configs.trace import get_trace_id


class TraceIdFilter(logging.Filter):
    def filter(self, record):
        record.trace_id = get_trace_id()
        return True


class JakartaFormatter(logging.Formatter):
    def formatTime(self, record, datefmt=None):
        dt = datetime.fromtimestamp(record.created, tz=timezone("Asia/Jakarta"))
        if datefmt:
            return dt.strftime(datefmt)
        return dt.isoformat()


def setup_logger(name="cron"):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.propagate = False  # ⛔ jangan ganggu root / bot logger

    # prevent duplicate handlers
    if logger.handlers:
        return logger

    logger.addFilter(TraceIdFilter())

    formatter = JakartaFormatter(
        "[%(asctime)s] [%(levelname)s] [%(trace_id)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger
