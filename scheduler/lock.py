import os

from scheduler.config import LAST_RUN_FILE, LOCK_FILE


def acquire_lock():
    if os.path.exists(LOCK_FILE):
        return False
    with open(LOCK_FILE, "w") as f:
        f.write(str(os.getpid()))
    return True

def release_lock():
    if os.path.exists(LOCK_FILE):
        os.remove(LOCK_FILE)

def read_last_run():
    if not os.path.exists(LAST_RUN_FILE):
        return None
    with open(LAST_RUN_FILE) as f:
        return f.read().strip()

def write_last_run(date_str):
    with open(LAST_RUN_FILE, "w") as f:
        f.write(date_str)
