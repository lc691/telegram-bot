from contextvars import ContextVar, Token
from typing import Optional

# ======================================================
# Context Variable
# ======================================================

_trace_id_ctx: ContextVar[str] = ContextVar(
    "trace_id",
    default="-",
)


# ======================================================
# Public API
# ======================================================

def set_trace_id(trace_id: Optional[str]) -> Token:
    """
    Set trace_id untuk context saat ini.

    Return:
        Token -> bisa dipakai untuk reset (optional)
    """
    return _trace_id_ctx.set(trace_id or "-")


def reset_trace_id(token: Token) -> None:
    """
    Reset trace_id ke nilai sebelumnya (jika perlu).
    """
    _trace_id_ctx.reset(token)


def get_trace_id() -> str:
    """
    Ambil trace_id aktif untuk context saat ini.
    """
    return _trace_id_ctx.get()
