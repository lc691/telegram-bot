from configs.logging_setup import log


def audit_log(action: str, user_id: int, meta: str = ""):
    log.info(f"[AUDIT][REFERRAL] action={action} user={user_id} {meta}")