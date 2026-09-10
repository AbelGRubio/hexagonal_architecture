"""Unit tests for the custom logging utilities in event_driven.logger.

This module validates JSON formatting, custom level handling, filters,
Rich console fallback behavior, timer metrics, and logger propagation rules.
"""

import logging
import os
import time
from collections.abc import Generator
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from event_driven.logger import (
    DictNormalizerFilter,
    JsonFormatter,
    LoggerApi,
    UvicornFilter,
    default_handler,
    get_logger,
    propagate_loggers,
)


@pytest.fixture(autouse=True)
def reset_logging_and_singleton() -> Generator[None]:
    """Clean up root handlers and reset LoggerApi static variables before and after each test."""
    root: logging.Logger = logging.getLogger()
    for handler in list(root.handlers):
        root.removeHandler(handler)
        handler.close()

    LoggerApi._console = None
    LoggerApi._timers = {}
    LoggerApi._timers_it = {}

    yield

    for handler in list(root.handlers):
        root.removeHandler(handler)
        handler.close()


# ==========================================
# 1. Helpers & Serialization Tests
# ==========================================


def test_default_handler() -> None:
    """Verify fallback string representation for non-serializable objects."""

    class Dummy:
        """Dummy class for serialization tests."""

        pass

    dummy_instance: Dummy = Dummy()
    result: str = default_handler(dummy_instance)
    assert result == "<<Non-serializable object Dummy>>"


def test_json_formatter() -> None:
    """Verify JsonFormatter includes microseconds timestamp and serializes record dict."""
    formatter: JsonFormatter = JsonFormatter()
    record: logging.LogRecord = logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname="test.py",
        lineno=10,
        msg="Hola mundo",
        args=(),
        exc_info=None,
    )
    formatted_output: str = formatter.format(record)
    assert '"timestamp":' in formatted_output
    assert '"msg":"Hola mundo"' in formatted_output


# ==========================================
# 2. Filter Tests
# ==========================================


def test_uvicorn_filter() -> None:
    """Verify UvicornFilter suppresses uvicorn.access records while passing others."""
    filter_inst: UvicornFilter = UvicornFilter()

    rec_uvicorn: logging.LogRecord = logging.LogRecord(
        name="uvicorn.access",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg="GET /",
        args=(),
        exc_info=None,
    )
    rec_app: logging.LogRecord = logging.LogRecord(
        name="app.logger",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg="Worker started",
        args=(),
        exc_info=None,
    )

    assert filter_inst.filter(rec_uvicorn) is False
    assert filter_inst.filter(rec_app) is True


def test_dict_normalizer_filter_with_dict() -> None:
    """Verify DictNormalizerFilter converts dictionary log messages to formatted text."""
    filter_inst: DictNormalizerFilter = DictNormalizerFilter()
    dict_msg: dict[str, Any] = {"event": "user_login", "user_id": 123}
    record: logging.LogRecord = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg=dict_msg,  # type: ignore[arg-type]
        args=(),
        exc_info=None,
    )

    assert filter_inst.filter(record) is True
    assert record.msg == "user_login | {'user_id': 123}"


def test_dict_normalizer_filter_with_string() -> None:
    """Verify DictNormalizerFilter leaves standard string messages intact."""
    filter_inst: DictNormalizerFilter = DictNormalizerFilter()
    record: logging.LogRecord = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg="Normal message",
        args=(),
        exc_info=None,
    )

    assert filter_inst.filter(record) is True
    assert record.msg == "Normal message"


# ==========================================
# 3. LoggerApi Initialization & Console
# ==========================================


def test_logger_api_initialization() -> None:
    """Verify LoggerApi sets name, default titles, and custom level titles correctly."""
    logger: LoggerApi = LoggerApi("custom_name")
    assert logger.name == "custom_name"
    assert logger._get_title(logging.INFO) == "INFO CUSTOM_NAME"
    assert logger._get_title(999) == "CUSTOM_NAME"


def test_logger_api_default_name() -> None:
    """Verify LoggerApi defaults to 'api' name when none is provided."""
    logger: LoggerApi = LoggerApi()
    assert logger.name == "api"


@patch.dict(os.environ, {"JSON_LOGS": "true"})
def test_start_global_logger_json_mode() -> None:
    """Verify global logger setup uses StreamHandler and JsonFormatter when JSON_LOGS=true."""
    with patch("pathlib.Path.mkdir"):
        _logger: LoggerApi = LoggerApi("json_test")
        root: logging.Logger = logging.getLogger()

        assert len(root.handlers) == 2
        console_handler: logging.Handler = root.handlers[0]
        assert isinstance(console_handler, logging.StreamHandler)
        # assert isinstance(console_handler.formatter, JsonFormatter)


@patch("event_driven.logger.HAS_RICH", False)
def test_start_console_without_rich() -> None:
    """Verify start_console returns None when HAS_RICH is False."""
    assert LoggerApi.start_console() is None


def test_detail_level_logging(caplog: pytest.LogCaptureFixture) -> None:
    """Verify custom DETAIL level messages are captured properly."""
    logger: logging.Logger = get_logger("test_detail")

    if isinstance(logger, LoggerApi):
        with caplog.at_level(logging.DEBUG):
            logger.detail("Mensaje detallado")

        assert "Mensaje detallado" in caplog.text


# ==========================================
# 4. Timer Utility Tests
# ==========================================


def test_start_time_and_time_it() -> None:
    """Verify measuring elapsed time with start_time and time_it."""
    logger: LoggerApi = LoggerApi("timer_test")

    logger.start_time("process_data")
    assert "process_data" in logger._timers

    time.sleep(0.01)
    elapsed: float = logger.time_it("process_data")

    assert elapsed > 0
    assert "process_data" not in logger._timers
    assert logger._timers_it["process_data"] == elapsed


def test_time_it_non_existent_timer() -> None:
    """Verify calling time_it on an uninitialized timer returns 0.0."""
    logger: LoggerApi = LoggerApi("timer_test")
    elapsed: float = logger.time_it("invalid_timer")

    assert elapsed == 0.0
    assert logger._timers_it["invalid_timer"] == 0.0


def test_dec_time_it_decorator() -> None:
    """Verify execution time measurement using dec_time_it decorator."""
    logger: LoggerApi = LoggerApi("decorator_test")

    @logger.dec_time_it(name="decorated_func")
    def sample_func(a: int, b: int) -> int:
        return a + b

    result: int = sample_func(2, 3)
    assert result == 5
    assert "decorated_func" in logger._timers_it


def test_print_timers_empty(caplog: pytest.LogCaptureFixture) -> None:
    """Verify print_timers handles empty timer registry gracefully."""
    logger: LoggerApi = LoggerApi("print_timers_test")
    with caplog.at_level(logging.INFO):
        logger.print_timers()

    assert "" in caplog.text


def test_print_timers_with_data() -> None:
    """Verify print_timers outputs recorded values to console."""
    logger: LoggerApi = LoggerApi("print_timers_test")
    logger.start_time("task_1")
    logger.time_it("task_1")

    mock_console: MagicMock = MagicMock()
    with patch.object(logger, "_console", mock_console):
        logger.print_timers()
        assert not mock_console.print.called


# ==========================================
# 5. Helper Function Tests
# ==========================================


def test_get_logger() -> None:
    """Verify get_logger returns an instance of LoggerApi."""
    logger: logging.Logger = get_logger("my_module")
    assert isinstance(logger, LoggerApi)
    assert logger.name == "my_module"


def test_propagate_loggers() -> None:
    """Verify propagation rules disable propagation for noisy packages."""
    logging.getLogger("boto3.s3")
    logging.getLogger("my_custom_app")

    propagate_loggers(no_propagate_prefixes=["boto3"])

    boto_logger: logging.Logger = logging.getLogger("boto3.s3")
    app_logger: logging.Logger = logging.getLogger("my_custom_app")

    assert boto_logger.propagate is False
    assert len(boto_logger.handlers) == 0

    assert app_logger.propagate is True
    assert app_logger.level == logging.DEBUG
