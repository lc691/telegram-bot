# utils/ttl_cache.py

import asyncio
import time

from typing import Dict


class TTLCache:
    def __init__(self, ttl: float = 3.0):
        self.ttl = ttl
        self._store: Dict[str, float] = {}
        self._lock = asyncio.Lock()

    async def acquire(self, key: str) -> bool:
        """
        Return:
            True  -> allowed
            False -> blocked (double click)
        """
        now = time.monotonic()

        async with self._lock:
            expire_at = self._store.get(key)

            if expire_at and expire_at > now:
                return False

            self._store[key] = now + self.ttl
            return True

    async def cleanup(self):
        now = time.monotonic()
        async with self._lock:
            self._store = {
                k: v for k, v in self._store.items()
                if v > now
            }
