# services/config.py

import os

CHECK_INTERVAL_SECONDS = int(os.getenv("VIP_CHECK_INTERVAL", 1800))  # default 30 menit
