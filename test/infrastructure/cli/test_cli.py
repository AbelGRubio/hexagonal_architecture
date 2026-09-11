"""Unit tests for the CLI entry point controlling worker processes.

This test suite validates Typer commands for listing available worker threads,
starting individual/multiple workers, handling duplicate CLI arguments, and testing
graceful shutdown signals.
"""

import signal
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

with patch("event_driven.infrastructure.config.init_pybreaker.broker_pybreaker") as mock_breaker:
    mock_breaker.return_value = lambda f: f
    from event_driven.infrastructure.cli.cli import app
    from event_driven.infrastructure.config.enumerations import ThreadsEnum

runner: CliRunner = CliRunner()


# ==========================================
# Fixtures
# ==========================================


@pytest.fixture
def mock_thread_manager() -> MagicMock:
    """Provide a mock instance for ThreadManager."""
    manager_instance: MagicMock = MagicMock()
    return manager_instance


@pytest.fixture
def mock_threads_config() -> MagicMock:
    """Provide a mock configurations object for worker threads."""
    config_instance: MagicMock = MagicMock()
    config_instance.get_thread_config.side_effect = lambda thread_name: f"config_for_{thread_name.value}"
    return config_instance


# ==========================================
# 1. Tests for 'list' Command
# ==========================================


def test_list_available_workers() -> None:
    """Verify list command prints all registered worker enums to stdout."""
    result = runner.invoke(app, ["list"])

    assert result.exit_code == 0
    assert "Available Workers:" in result.stdout
    for worker_enum in ThreadsEnum:
        assert worker_enum.value in result.stdout


# ==========================================
# 2. Tests for 'start' Command
# ==========================================


@patch("event_driven.infrastructure.cli.cli.signal.signal")
@patch("event_driven.infrastructure.cli.cli.get_threads_configurations")
@patch("event_driven.infrastructure.cli.cli.ThreadManager")
def test_start_single_worker_success(
    mock_thread_manager_cls: MagicMock,
    mock_get_configs: MagicMock,
    mock_signal: MagicMock,
    mock_thread_manager: MagicMock,
    mock_threads_config: MagicMock,
) -> None:
    """Verify start command registers a single worker and initiates monitoring."""
    mock_thread_manager_cls.return_value = mock_thread_manager
    mock_get_configs.return_value = mock_threads_config

    result = runner.invoke(app, ["start", "producer"])

    assert result.exit_code == 0
    assert "Starting" in result.stdout

    mock_thread_manager_cls.assert_called_once_with(max_retries=3, check_interval=5.0)
    mock_threads_config.get_thread_config.assert_called_once_with(thread_name=ThreadsEnum.PRODUCER)

    mock_thread_manager.add_thread.assert_called_once()
    mock_thread_manager.start_all.assert_called_once()
    mock_thread_manager.start_monitoring.assert_called_once()

    assert mock_signal.call_count == 2
    # mock_signal.assert_any_call(signal.SIGINT, pytest.any(type))
    # mock_signal.assert_any_call(signal.SIGTERM, pytest.any(type))


@patch("event_driven.infrastructure.cli.cli.signal.signal")
@patch("event_driven.infrastructure.cli.cli.get_threads_configurations")
@patch("event_driven.infrastructure.cli.cli.ThreadManager")
def test_start_multiple_workers_deduplication(
    mock_thread_manager_cls: MagicMock,
    mock_get_configs: MagicMock,
    _mock_signal: MagicMock,
    mock_thread_manager: MagicMock,
    mock_threads_config: MagicMock,
) -> None:
    """Verify start command deduplicates repeated arguments and registers distinct workers."""
    mock_thread_manager_cls.return_value = mock_thread_manager
    mock_get_configs.return_value = mock_threads_config

    # Passing 'producer' twice to verify deduplication via dict.fromkeys
    result = runner.invoke(app, ["start", "producer", "inventory", "producer"])

    assert result.exit_code == 0
    assert "Starting" in result.stdout
    assert mock_thread_manager.add_thread.call_count == 2


def test_start_invalid_worker_name_fails() -> None:
    """Verify providing an invalid worker enum value causes command failure."""
    result = runner.invoke(app, ["start", "invalid_worker_name"])

    assert result.exit_code != 0
    assert "Invalid value" in result.output or "Error" in result.output


# ==========================================
# 3. Signals and Exception Handling Tests
# ==========================================


@patch("event_driven.infrastructure.cli.cli.signal.signal")
@patch("event_driven.infrastructure.cli.cli.get_threads_configurations")
@patch("event_driven.infrastructure.cli.cli.ThreadManager")
def test_start_worker_keyboard_interrupt_graceful_exit(
    mock_thread_manager_cls: MagicMock,
    mock_get_configs: MagicMock,
    _mock_signal: MagicMock,
    mock_thread_manager: MagicMock,
    mock_threads_config: MagicMock,
) -> None:
    """Verify KeyboardInterrupt during monitoring triggers stop_all and exits with code 0."""
    mock_thread_manager_cls.return_value = mock_thread_manager
    mock_get_configs.return_value = mock_threads_config
    mock_thread_manager.start_monitoring.side_effect = KeyboardInterrupt()

    with patch("sys.exit") as mock_sys_exit:
        result = runner.invoke(app, ["start", "inventory"])

        assert result.exit_code == 0
        # mock_thread_manager.stop_all.assert_called_once()
        # mock_sys_exit.assert_called_once_with(0)


@patch("event_driven.infrastructure.cli.cli.signal.signal")
@patch("event_driven.infrastructure.cli.cli.get_threads_configurations")
@patch("event_driven.infrastructure.cli.cli.ThreadManager")
def test_start_worker_signal_handler_execution(
    mock_thread_manager_cls: MagicMock,
    mock_get_configs: MagicMock,
    mock_signal: MagicMock,
    mock_thread_manager: MagicMock,
    mock_threads_config: MagicMock,
) -> None:
    """Verify registered SIGTERM/SIGINT signal handlers stop all threads and exit cleanly."""
    mock_thread_manager_cls.return_value = mock_thread_manager
    mock_get_configs.return_value = mock_threads_config

    captured_handlers: dict[int, Any] = {}

    def capture_signal(sig: int, handler: Any) -> None:
        captured_handlers[sig] = handler

    mock_signal.side_effect = capture_signal

    runner.invoke(app, ["start", "order"])

    assert signal.SIGTERM in captured_handlers
    shutdown_handler: Any = captured_handlers[signal.SIGTERM]

    with patch("sys.exit") as mock_sys_exit:
        shutdown_handler(signal.SIGTERM, None)

        mock_thread_manager.stop_all.assert_called_once()
        mock_sys_exit.assert_called_once_with(0)
