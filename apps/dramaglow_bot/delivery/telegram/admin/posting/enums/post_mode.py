# enums/post_mode.py
from enum import Enum

class PostMode(str, Enum):
    MAIN = "main"                  # trigger repost via handler
    DISTRIBUTE_ONLY = "distribute_only"  # langsung backup + target
