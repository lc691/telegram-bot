from dataclasses import dataclass
from enum import Enum
from typing import Optional


class MatchStatus(str, Enum):
    EXACT = "exact"
    CONFIDENT = "confident"
    AMBIGUOUS = "ambiguous"
    NO_MATCH = "no_match"
    NO_FILE = "no_file"

    # OCR sekarang internal VPS → tidak perlu status khusus
    # OCR_SUGGEST, OCR_EMPTY HAPUS


@dataclass
class MatchResult:
    status: MatchStatus
    message: str

    best: Optional[dict] = None
    poster: Optional[str] = None
    gap: Optional[float] = None
    url: Optional[str] = None

    # =============================
    # 🏭 Factory (SAFE)
    # =============================
    @classmethod
    def from_best(
        cls,
        *,
        status: MatchStatus,
        best: dict,
        message: str,
        **kwargs,
    ) -> "MatchResult":
        return cls(
            status=status,
            message=message,
            best=best,
            poster=best.get("poster"),
            **kwargs,
        )
