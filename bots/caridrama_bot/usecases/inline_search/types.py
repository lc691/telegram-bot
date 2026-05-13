from dataclasses import dataclass
from enum import Enum
from typing import Optional, TypedDict


# ======================================
# 📦 DOMAIN ROW (NORMALIZED)
# ======================================


class ShowRow(TypedDict):
    show_id: int
    title: str
    channel_username: Optional[str]
    message_id: Optional[int]
    channel_id: Optional[int]  # lebih fleksibel


# ======================================
# 🧭 RESULT KIND
# ======================================


class ResultKind(str, Enum):
    SEARCH = "search"
    RANDOM = "random"
    TRENDING = "trending"
    POPULAR = "popular"
    FALLBACK = "fallback"


# ======================================
# 📊 SEARCH RESULT CONTAINER
# ======================================


@dataclass(slots=True)
class SearchResult:
    rows: list[ShowRow]
    kind: ResultKind
    has_more: bool = False  # 🔥 penting untuk pagination

    # -----------------------------
    # Semantic helpers
    # -----------------------------

    def is_fallback(self) -> bool:
        return self.kind is ResultKind.FALLBACK

    def is_search(self) -> bool:
        return self.kind is ResultKind.SEARCH

    def is_empty(self) -> bool:
        return not self.rows

    def is_paginated(self) -> bool:
        return self.has_more

    def __len__(self) -> int:
        return len(self.rows)

    # -----------------------------
    # Factory helpers
    # -----------------------------

    @classmethod
    def empty(cls, kind: ResultKind = ResultKind.FALLBACK) -> "SearchResult":
        return cls(rows=[], kind=kind, has_more=False)
