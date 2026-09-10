"""Unit tests for system information utilities.

This module validates logging functions for system hardware, software environment,
operating system specs, and memory calculation utilities using mocks and caplog.
"""

import sys
from unittest.mock import MagicMock, patch

import pytest

from event_driven.info import (
    get_memory_usage,
    info_hardware,
    info_os,
    info_software,
    info_system,
)

# ==========================================
# 1. Tests for OS and Environment Info
# ==========================================


@patch("platform.platform")
def test_info_os(
    mock_platform: MagicMock,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Verify info_os logs the platform information formatted correctly."""
    mock_platform.return_value = "Linux-5.15.0-generic-x86_64"

    with caplog.at_level("INFO"):
        info_os()

    mock_platform.assert_called_once()
    assert "OS" in caplog.text
    assert "Linux-5.15.0-generic-x86_64" in caplog.text


@patch("event_driven.info.INSTALLED_PACKAGES", {"httpx": "0.24.0", "pydantic": "2.5.0"})
@patch("platform.python_version")
def test_info_software_with_default_modules(
    mock_python_version: MagicMock,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Verify info_software logs default modules when no list is provided."""
    mock_python_version.return_value = "3.11.5"

    with caplog.at_level("INFO"):
        info_software()

    mock_python_version.assert_called_once()
    assert "PYTHON" in caplog.text
    assert "3.11.5" in caplog.text
    assert "httpx" in caplog.text
    assert "0.24.0" in caplog.text


@patch("event_driven.info.INSTALLED_PACKAGES", {"pydantic": "2.5.0"})
def test_info_software_with_custom_and_missing_modules(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Verify info_software logs custom modules and outputs 'N/A' for uninstalled ones."""
    custom_modules: list[str] = ["pydantic", "non_existent_package"]

    with caplog.at_level("INFO"):
        info_software(modules=custom_modules)

    assert "pydantic" in caplog.text
    assert "2.5.0" in caplog.text
    assert "non_existent_package" in caplog.text
    assert "N/A" in caplog.text


# ==========================================
# 2. Tests for Hardware Info
# ==========================================


@patch("psutil.virtual_memory")
@patch("psutil.cpu_count")
@patch("cpuinfo.get_cpu_info")
def test_info_hardware(
    mock_get_cpu_info: MagicMock,
    mock_cpu_count: MagicMock,
    mock_virtual_memory: MagicMock,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Verify info_hardware queries CPU and RAM info and formats the log message."""
    mock_get_cpu_info.return_value = {"brand_raw": "Intel(R) Core(TM) i7-10700 CPU @ 2.90GHz"}
    mock_cpu_count.return_value = 16

    mock_mem: MagicMock = MagicMock()
    # 16 GB en bytes (16 * 1024^3)
    mock_mem.total = 16 * 1024 * 1024 * 1024
    mock_virtual_memory.return_value = mock_mem

    with caplog.at_level("INFO"):
        info_hardware()

    mock_get_cpu_info.assert_called_once()
    mock_cpu_count.assert_called_once_with(logical=True)
    mock_virtual_memory.assert_called_once()

    assert "MACHINE" in caplog.text
    assert "Intel(R) Core(TM) i7-10700 CPU" in caplog.text
    assert "16 cores" in caplog.text
    assert "16 GB RAM" in caplog.text


@patch("psutil.virtual_memory")
@patch("psutil.cpu_count")
@patch("cpuinfo.get_cpu_info")
def test_info_hardware_fallback_cpu_brand(
    mock_get_cpu_info: MagicMock,
    mock_cpu_count: MagicMock,
    mock_virtual_memory: MagicMock,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Verify info_hardware falls back to 'Unknown CPU' when brand_raw key is missing."""
    mock_get_cpu_info.return_value = {}
    mock_cpu_count.return_value = 4
    mock_mem: MagicMock = MagicMock()
    mock_mem.total = 8 * 1024 * 1024 * 1024
    mock_virtual_memory.return_value = mock_mem

    with caplog.at_level("INFO"):
        info_hardware()

    assert "Unknown CPU" in caplog.text


# ==========================================
# 3. Tests for System Aggregate & Helpers
# ==========================================


@patch("time.ctime")
@patch("pathlib.Path.absolute")
@patch("event_driven.info.info_software")
@patch("event_driven.info.info_os")
@patch("event_driven.info.info_hardware")
def test_info_system(
    mock_info_hardware: MagicMock,
    mock_info_os: MagicMock,
    mock_info_software: MagicMock,
    mock_absolute: MagicMock,
    mock_ctime: MagicMock,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Verify info_system calls all sub-info functions and logs execution metadata."""
    mock_absolute.return_value = "/mock/path/project"
    mock_ctime.return_value = "Wed Sep 9 10:00:00 2026"
    custom_modules: list[str] = ["requests"]

    with caplog.at_level("INFO"):
        info_system(modules=custom_modules)

    mock_info_hardware.assert_called_once()
    mock_info_os.assert_called_once()
    mock_info_software.assert_called_once_with(custom_modules)

    assert "EXECUTION PATH" in caplog.text
    assert "/mock/path/project" in caplog.text
    assert "EXECUTION DATE" in caplog.text
    assert "Wed Sep 9 10:00:00 2026" in caplog.text


def test_get_memory_usage() -> None:
    """Verify get_memory_usage calculates object size in megabytes accurately."""
    sample_data: list[int] = list(range(10000))
    expected_mb: float = round(sys.getsizeof(sample_data) / (1024**2), 3)

    result_mb: float = get_memory_usage(sample_data)

    assert isinstance(result_mb, float)
    assert result_mb == expected_mb
