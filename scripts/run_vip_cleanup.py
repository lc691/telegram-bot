import traceback
from datetime import datetime, timezone
from configs.trace import set_trace_id, reset_trace_id

from configs.logging_setup import log
from scheduler.jobs.vip_cleanup.context import cron_context
from scheduler.jobs.vip_cleanup.free_access import reset_non_vip_free_access
from scheduler.jobs.vip_cleanup.vip_actions import deactivate_expired
from scheduler.jobs.vip_cleanup.vip_stats import count_active_vips
from config import BOT_USERNAME


# ===============================
# CRON MAIN
# ===============================
def run_vip_cleanup():

    now_utc = datetime.now(timezone.utc)
    trace_id = f"CRON-VIP-{now_utc.strftime('%Y%m%d%H%M%S')}"
    token = set_trace_id(trace_id)
    try:
        ctx = cron_context()

        # --- START ---
        log.info(
            "[CRON][START] VIP Cleanup | UTC=%s | WIB=%s",
            ctx["utc"],
            ctx["wib"],
        )

        before = count_active_vips()
        log.info("[CRON][STEP 0] VIP aktif sebelum cleanup: %s", before)

        results = {
            "deactivated": {
                "label": "Deactivate Expired VIPs",
                "count": 0,
                "status": "✅",
                "error": None,
            },
            "reset": {
                "label": "Reset Free Access",
                "count": 0,
                "status": "✅",
                "error": None,
            },
        }

        # STEP 1: Deactivate expired VIP
        try:
            results["deactivated"]["count"] = deactivate_expired(BOT_USERNAME)
            log.info(
                "[CRON][STEP 1] VIP dinonaktifkan: %s",
                results["deactivated"]["count"],
            )
        except Exception:
            log.exception("[CRON][STEP 1] Error deactivate VIP")
            results["deactivated"]["status"] = "❌"
            results["deactivated"]["error"] = traceback.format_exc(limit=3)

        # STEP 2: Reset free access non-VIP
        try:
            results["reset"]["count"] = reset_non_vip_free_access()
            log.info(
                "[CRON][STEP 2] Reset free access: %s",
                results["reset"]["count"],
            )
        except Exception:
            log.exception("[CRON][STEP 2] Error reset free access")
            results["reset"]["status"] = "❌"
            results["reset"]["error"] = traceback.format_exc(limit=3)

        after = count_active_vips()
        log.info("[CRON][STEP 3] VIP aktif setelah cleanup: %s", after)

        # --- SUMMARY (LOG ONLY) ---
        summary_msg = "VIP Cleanup Finished\n" f"Before: {before}\n" f"After: {after}\n"

        for step in results.values():
            summary_msg += f"{step['status']} {step['label']}: {step['count']}\n"
            if step["error"]:
                summary_msg += f"Error:\n{step['error']}\n"

        log.info("[CRON][FINISH] VIP Cleanup Finished")
        log.info(summary_msg)
    finally:
        reset_trace_id(token)


# ===============================
# ENTRYPOINT
# ===============================
if __name__ == "__main__":
    from configs.logging_setup import setup_logger

    setup_logger()
    run_vip_cleanup()
