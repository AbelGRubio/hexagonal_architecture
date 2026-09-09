"""Unit tests for the event-driven core application entrypoint.

This module validates thread registration, signal handling setup, health monitoring,
and graceful shutdown logic triggered during application execution.
"""

import signal

from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from event_driven.core import main
from event_driven.infrastructure.config.enumerations import ThreadsEnum


# ==========================================
# Fixtures
# ==========================================


@pytest.fixture
def mock_thread_manager() -> MagicMock:
    """Provide a mock instance of ThreadManager."""
    manager_instance: MagicMock = MagicMock()
    return manager_instance


@pytest.fixture
def mock_threads_config() -> MagicMock:
    """Provide a mock configurations object containing thread settings."""
    config_instance: MagicMock = MagicMock()
    config_instance.get_thread_config.side_effect = lambda thread_name: f"config_for_{thread_name.value}"
    return config_instance


# ==========================================
# 1. Main Execution & Registration Tests
# ==========================================


@patch("event_driven.core.signal.signal")
@patch("event_driven.core.get_threads_configurations")
@patch("event_driven.core.ThreadManager")
def test_main_successful_execution_and_thread_registration(
    mock_thread_manager_cls: MagicMock,
    mock_get_configs: MagicMock,
    mock_signal: MagicMock,
    mock_thread_manager: MagicMock,
    mock_threads_config: MagicMock,
) -> None:
    """Verify main registers all worker threads, installs signals, and starts monitoring."""
    mock_thread_manager_cls.return_value = mock_thread_manager
    mock_get_configs.return_value = mock_threads_config

    main()

    # 1. Verify ThreadManager instantiation
    mock_thread_manager_cls.assert_called_once_with(max_retries=3, check_interval=5.0)

    # 2. Verify all 5 worker threads were registered
    assert mock_thread_manager.add_thread.call_count == 5

    registered_enums: list[ThreadsEnum] = [
        ThreadsEnum.PRODUCER,
        ThreadsEnum.INVENTORY,
        ThreadsEnum.ORDER,
        ThreadsEnum.PAYMENT,
        ThreadsEnum.NOTIFICATION,
    ]

    for thread_enum in registered_enums:
        mock_threads_config.get_thread_config.assert_any_call(thread_name=thread_enum)

    # 3. Verify signal handlers installation
    assert mock_signal.call_count == 2
    # mock_signal.assert_any_call(signal.SIGINT, pytest.Any(type))
    # mock_signal.assert_any_call(signal.SIGTERM, pytest.any(type))

    # 4. Verify thread lifecycle execution
    mock_thread_manager.start_all.assert_called_once()
    mock_thread_manager.start_monitoring.assert_called_once()


# ==========================================
# 2. Signal & Shutdown Tests
# ==========================================


@patch("event_driven.core.signal.signal")
@patch("event_driven.core.get_threads_configurations")
@patch("event_driven.core.ThreadManager")
def test_main_keyboard_interrupt_triggers_graceful_shutdown(
    mock_thread_manager_cls: MagicMock,
    mock_get_configs: MagicMock,
    _mock_signal: MagicMock,
    mock_thread_manager: MagicMock,
    mock_threads_config: MagicMock,
) -> None:
    """Verify KeyboardInterrupt exception triggers graceful thread manager stop and sys.exit."""
    mock_thread_manager_cls.return_value = mock_thread_manager
    mock_get_configs.return_value = mock_threads_config
    mock_thread_manager.start_monitoring.side_effect = KeyboardInterrupt()

    with patch("sys.exit") as mock_sys_exit:
        main()

        mock_thread_manager.stop_all.assert_called_once()
        mock_sys_exit.assert_called_once_with(0)


@patch("event_driven.core.signal.signal")
@patch("event_driven.core.get_threads_configurations")
@patch("event_driven.core.ThreadManager")
def test_signal_shutdown_handler_execution(
    mock_thread_manager_cls: MagicMock,
    mock_get_configs: MagicMock,
    mock_signal: MagicMock,
    mock_thread_manager: MagicMock,
    mock_threads_config: MagicMock,
) -> None:
    """Verify captured signal handler directly invokes manager.stop_all and terminates process."""
    mock_thread_manager_cls.return_value = mock_thread_manager
    mock_get_configs.return_value = mock_threads_config

    captured_handlers: dict[int, Any] = {}

    def capture_signal(sig: int, handler: Any) -> None:
        captured_handlers[sig] = handler

    mock_signal.side_effect = capture_signal

    main()

    assert signal.SIGTERM in captured_handlers
    shutdown_handler: Any = captured_handlers[signal.SIGTERM]

    with patch("sys.exit") as mock_sys_exit:
        shutdown_handler(signal.SIGTERM, None)

        mock_thread_manager.stop_all.assert_called_once()
        mock_sys_exit.assert_called_once_with(0)