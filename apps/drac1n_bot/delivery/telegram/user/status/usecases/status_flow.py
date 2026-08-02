from ..presenters.status_context import build_status_context


class StatusFlowResult:
    def __init__(self, *, blocked: bool, message: str | None, context: dict | None):
        self.blocked = blocked
        self.message = message
        self.context = context


def run_status_flow(*, user_id: int, admin_cache, user) -> StatusFlowResult:
    """
    STATUS = NON-UI FLOW
    - Tidak mengunci apa pun
    - Sinkron penuh
    - Aman dipanggil dari handler mana pun
    """

    try:
        context = build_status_context(
            user_id=user_id,
            user=user,
            admin_cache=admin_cache,
        )

        return StatusFlowResult(
            blocked=False,
            message=None,
            context=context,
        )

    except Exception:
        return StatusFlowResult(
            blocked=True,
            message="⚠️ Gagal memuat status.",
            context=None,
        )
