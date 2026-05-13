from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import common.task.vip_auto_cleanup as mod


class FakeClient:
    def __init__(self, connected=True):
        self.is_connected = connected

@pytest.mark.asyncio
async def test_cleanup_skipped_when_client_disconnected():
    client = FakeClient(connected=False)

    with patch.object(mod, "_run_cleanup_in_thread") as run_mock:
        await mod.vip_cleanup_task(client)

        run_mock.assert_not_called()

@pytest.mark.asyncio
async def test_cleanup_success_flow():
    client = FakeClient(connected=True)

    with (
        patch.object(mod, "_run_cleanup_in_thread", return_value=(5, 10)) as run_mock,
        patch.object(mod, "notify_admin_info", new_callable=AsyncMock) as notif_mock,
    ):
        await mod.vip_cleanup_task(client)

        run_mock.assert_called_once()
        notif_mock.assert_called_once()

        msg = notif_mock.call_args.args[1]
        assert "5 VIP expired" in msg
        assert "10 status VIP" in msg

@pytest.mark.asyncio
async def test_cleanup_db_error_handled():
    client = FakeClient(connected=True)

    with (
        patch.object(
            mod,
            "_run_cleanup_in_thread",
            side_effect=RuntimeError("DB down"),
        ),
        patch.object(mod, "notify_admin_error", new_callable=AsyncMock) as err_notif,
    ):
        await mod.vip_cleanup_task(client)

        err_notif.assert_called_once()
        msg = err_notif.call_args.args[1]
        assert "RuntimeError" in msg
        assert "DB down" in msg

@pytest.mark.asyncio
async def test_notification_error_does_not_crash():
    client = FakeClient(connected=True)

    with (
        patch.object(mod, "_run_cleanup_in_thread", side_effect=ValueError("fail")),
        patch.object(
            mod,
            "notify_admin_error",
            side_effect=Exception("Telegram down"),
        ),
    ):
        # Tidak boleh raise
        await mod.vip_cleanup_task(client)

def test_scheduler_idempotent_start():
    client = FakeClient()

    with patch.object(mod, "AsyncIOScheduler") as sched_mock:
        sched_instance = MagicMock()
        sched_instance.running = False

        def start_side_effect():
            sched_instance.running = True

        sched_instance.start.side_effect = start_side_effect
        sched_mock.return_value = sched_instance

        mod.start_vip_auto_cleanup(client)
        mod.start_vip_auto_cleanup(client)

        sched_instance.start.assert_called_once()


def test_scheduler_stop():
    with patch.object(mod, "_scheduler") as sched:
        sched.running = True

        mod.stop_vip_auto_cleanup()

        sched.shutdown.assert_called_once()
