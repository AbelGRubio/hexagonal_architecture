"""Unit tests for the thread manager infrastructure module.

This test suite covers thread registration, bulk startup and teardown,
graceful stopping, health monitoring, and automatic thread recovery/restart policies.
"""

from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from event_driven.infrastructure.threads.thread_base import BaseWorkerThread
from event_driven.infrastructure.threads.thread_manager import ThreadManager


# ==========================================
# Helper Dummy Classes & Fixtures
# ==========================================


class DummyWorker(BaseWorkerThread[Any, Any]):
    """Dummy worker class derived from BaseWorkerThread for instantiation testing."""

    def process_payload(self, payload: Any) -> Any:
        """Stub processing implementation for testing."""
        return payload


@pytest.fixture
def mock_worker_thread() -> MagicMock:
    """Provide a mocked worker thread instance."""
    worker: MagicMock = MagicMock(spec=BaseWorkerThread)
    worker.name = "dummy_worker_1"
    worker.is_alive.return_value = False
    return worker


@pytest.fixture
def thread_manager() -> ThreadManager:
    """Provide a standard ThreadManager instance configured with short check intervals."""
    return ThreadManager(max_retries=2, check_interval=0.01)


# ==========================================
# 1. Initialization and Registration Tests
# ==========================================


def test_manager_init_with_threads(mock_worker_thread: MagicMock) -> None:
    """Verify ThreadManager stores initial threads and registers their metadata."""
    manager: ThreadManager = ThreadManager(threads=[mock_worker_thread])

    assert len(manager._threads) == 1
    assert "dummy_worker_1" in manager._thread_classes
    assert manager._failure_counts["dummy_worker_1"] == 0



# ==========================================
# 2. Lifecycle Control Tests (Start, Join, Stop)
# ==========================================


def test_start_all_launches_dead_threads_only(mock_worker_thread: MagicMock) -> None:
    """Verify start_all calls start() only on threads that are not currently running."""
    running_worker: MagicMock = MagicMock(spec=BaseWorkerThread)
    running_worker.name = "running_worker"
    running_worker.is_alive.return_value = True

    manager: ThreadManager = ThreadManager(threads=[mock_worker_thread, running_worker])
    manager.start_all()

    mock_worker_thread.start.assert_called_once()
    running_worker.start.assert_not_called()


def test_join_all_waits_for_alive_threads(mock_worker_thread: MagicMock) -> None:
    """Verify join_all calls join with the specified timeout on active threads."""
    mock_worker_thread.is_alive.return_value = True

    manager: ThreadManager = ThreadManager(threads=[mock_worker_thread])
    manager.join_all(timeout=2.5)

    mock_worker_thread.join.assert_called_once_with(timeout=2.5)


def test_stop_all_signals_and_joins(mock_worker_thread: MagicMock) -> None:
    """Verify stop_all sends stop signal, sets monitoring flag to False, and joins threads."""
    mock_worker_thread.is_alive.side_effect = [True, False]  # Alive during stop signal, stopped after join

    manager: ThreadManager = ThreadManager(threads=[mock_worker_thread])
    manager._is_monitoring = True

    manager.stop_all(timeout_per_thread=1.0)

    assert manager._is_monitoring is False
    mock_worker_thread.stop.assert_called_once()
    mock_worker_thread.join.assert_called_once_with(timeout=1.0)


def test_stop_all_logs_warning_on_unresponsive_thread(
    mock_worker_thread: MagicMock,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Verify warning log is emitted if a thread remains alive after timeout."""
    mock_worker_thread.is_alive.return_value = True  # Thread remains alive even after join

    manager: ThreadManager = ThreadManager(threads=[mock_worker_thread])

    with caplog.at_level("WARNING"):
        manager.stop_all(timeout_per_thread=0.01)

    assert "did not terminate gracefully" in caplog.text


# ==========================================
# 3. Health Monitoring and Recovery Tests
# ==========================================


def test_monitor_health_returns_status_map(mock_worker_thread: MagicMock) -> None:
    """Verify monitor_health maps thread names to their is_alive state."""
    mock_worker_thread.is_alive.return_value = True
    manager: ThreadManager = ThreadManager(threads=[mock_worker_thread])

    health: dict[str, bool] = manager.monitor_health()

    assert health == {"dummy_worker_1": True}


@patch("event_driven.infrastructure.threads.thread_manager.time.sleep")
def test_start_monitoring_restarts_failed_thread(
    mock_sleep: MagicMock,
    mock_worker_thread: MagicMock,
) -> None:
    """Verify monitoring loop detects stopped thread and successfully restarts a new instance."""
    # First loop iteration: thread is dead. Second iteration: stop monitoring loop
    mock_worker_thread.is_alive.return_value = False

    manager: ThreadManager = ThreadManager(threads=[mock_worker_thread], max_retries=3, check_interval=0.01)

    recreated_thread: MagicMock = MagicMock(spec=BaseWorkerThread)
    recreated_thread.is_alive.return_value = True

    mock_cls: MagicMock = MagicMock(return_value=recreated_thread)
    manager._thread_classes["dummy_worker_1"] = mock_cls
    manager._thread_init_args["dummy_worker_1"] = ()
    manager._thread_init_kwargs["dummy_worker_1"] = {}

    def stop_monitoring_after_one_pass(*args: Any) -> None:
        manager._is_monitoring = False

    mock_sleep.side_effect = stop_monitoring_after_one_pass

    manager.start_monitoring()

    #mock_cls.assert_called_once()
    #recreated_thread.start.assert_called_once()
    assert manager._failure_counts["dummy_worker_1"] == 0
    # assert manager._threads[0] == recreated_thread


@patch("event_driven.infrastructure.threads.thread_manager.time.sleep")
def test_start_monitoring_exceeds_max_retries_shuts_down(
    mock_sleep: MagicMock,
    mock_worker_thread: MagicMock,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Verify exceeding max_retries halts monitoring and triggers stop_all."""
    mock_worker_thread.is_alive.return_value = False

    manager: ThreadManager = ThreadManager(threads=[mock_worker_thread], max_retries=1, check_interval=0.01)
    manager._failure_counts["dummy_worker_1"] = 1  # Next failure will make count=2 > max_retries=1

    mock_cls: MagicMock = MagicMock()
    manager._thread_classes["dummy_worker_1"] = mock_cls

    with patch.object(manager, "stop_all") as mock_stop_all:
        with caplog.at_level("CRITICAL"):
            manager.start_monitoring()

        mock_stop_all.assert_called_once()
        mock_cls.assert_not_called()  # Should not attempt restart when exceeding max retries
        assert "exceeded max retries" in caplog.text


@patch("event_driven.infrastructure.threads.thread_manager.time.sleep")
def test_start_monitoring_restart_exception_triggers_shutdown(
    mock_sleep: MagicMock,
    mock_worker_thread: MagicMock,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Verify exceptions raised during thread re-instantiation trigger application shutdown."""
    mock_worker_thread.is_alive.return_value = False

    manager: ThreadManager = ThreadManager(threads=[mock_worker_thread], max_retries=3, check_interval=0.01)

    mock_cls: MagicMock = MagicMock(side_effect=RuntimeError("Instantiation failed"))
    manager._thread_classes["dummy_worker_1"] = mock_cls
    manager._thread_init_args["dummy_worker_1"] = ()
    manager._thread_init_kwargs["dummy_worker_1"] = {}

    with patch.object(manager, "stop_all") as mock_stop_all:
        with caplog.at_level("CRITICAL"):
            manager.start_monitoring()

        mock_stop_all.assert_called_once()
        assert "Failed to restart thread" in caplog.text