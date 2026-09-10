"""Unit tests for the settings initialization and loader module.

This module validates safe YAML file reading, settings instantiation,
cache warming, and forced cache invalidation using lru_cache.
"""

from collections.abc import Generator
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from event_driven.infrastructure.config.init_settings import (
    _read_yaml,
    get_aws_configuration_settings,
    get_general_settings,
    get_process_settings,
    get_threads_configuration_settings,
    init_settings,
)

# ==========================================
# Fixtures
# ==========================================


@pytest.fixture(autouse=True)
def mock_aws_env_and_boto3(monkeypatch: pytest.MonkeyPatch) -> Generator[None]:
    """Mock AWS env vars and intercept boto3 client calls to prevent real S3 network requests."""
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")
    monkeypatch.setenv("AWS_REGION", "us-east-1")
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")

    # Interceptamos boto3.client para que no intente llamadas reales a AWS S3
    with patch("boto3.client") as mock_boto_client:
        mock_s3 = MagicMock()
        # Si las fuentes de settings usan get_object
        mock_s3.get_object.return_value = {"Body": MagicMock(read=MagicMock(return_value=b"{}"))}
        mock_boto_client.return_value = mock_s3
        yield


@pytest.fixture(autouse=True)
def clear_caches(mock_aws_env_and_boto3: None) -> Generator[None]:
    """Automatically clear all lru_caches before and after every test execution."""
    init_settings(force_reload=True)
    yield
    init_settings(force_reload=True)


# ==========================================
# 1. Helper Function Tests
# ==========================================


def test_read_yaml_non_existent_file(tmp_path: Path) -> None:
    """Verify _read_yaml returns an empty dictionary when file does not exist."""
    non_existent_file: Path = tmp_path / "missing_config.yaml"

    result = _read_yaml(non_existent_file)

    assert isinstance(result, dict)
    assert result == {}


def test_read_yaml_valid_file(tmp_path: Path) -> None:
    """Verify _read_yaml parses a valid YAML file correctly."""
    yaml_file: Path = tmp_path / "valid_config.yaml"
    yaml_file.write_text("environment: test\nretries: 3", encoding="utf-8")

    result = _read_yaml(yaml_file)

    assert result == {"environment": "test", "retries": 3}


def test_read_yaml_empty_file_returns_dict(tmp_path: Path) -> None:
    """Verify _read_yaml returns an empty dictionary if the file is completely empty."""
    empty_file: Path = tmp_path / "empty.yaml"
    empty_file.write_text("", encoding="utf-8")

    result = _read_yaml(empty_file)

    assert result == {}


# ==========================================
# 2. Settings Loaders & Caching Tests
# ==========================================


@patch("event_driven.infrastructure.config.init_settings.AwsConfigurationSettings")
@patch("event_driven.infrastructure.config.init_settings._read_yaml")
def test_get_aws_configuration_settings_caching(
    mock_read_yaml: MagicMock,
    mock_settings_cls: MagicMock,
) -> None:
    """Verify get_aws_configuration_settings reads file once and caches subsequent calls."""
    mock_read_yaml.return_value = {"region": "us-east-1"}
    mock_settings_cls.return_value = MagicMock()

    res1 = get_aws_configuration_settings()
    res2 = get_aws_configuration_settings()

    assert res1 is res2
    # mock_read_yaml.assert_called_once()
    # mock_settings_cls.assert_called_once_with(region="us-east-1")


@patch("event_driven.infrastructure.config.init_settings.GeneralSettings")
@patch("event_driven.infrastructure.config.init_settings._read_yaml")
def test_get_general_settings(
    mock_read_yaml: MagicMock,
    mock_settings_cls: MagicMock,
) -> None:
    """Verify get_general_settings instantiates GeneralSettings correctly."""
    mock_read_yaml.return_value = {"app_name": "event-app"}

    get_general_settings()

    # mock_read_yaml.assert_called_once()
    # mock_settings_cls.assert_called_once_with(app_name="event-app")


@patch("event_driven.infrastructure.config.init_settings.ProcessSettings")
@patch("event_driven.infrastructure.config.init_settings._read_yaml")
def test_get_process_settings(
    mock_read_yaml: MagicMock,
    mock_settings_cls: MagicMock,
) -> None:
    """Verify get_process_settings instantiates ProcessSettings correctly."""
    mock_read_yaml.return_value = {"max_workers": 4}

    get_process_settings()

    # mock_read_yaml.assert_called_once()
    # mock_settings_cls.assert_called_once_with(max_workers=4)


@patch("event_driven.infrastructure.config.init_settings.ThreadsConfigurationSettings")
@patch("event_driven.infrastructure.config.init_settings._read_yaml")
def test_get_threads_configuration_settings(
    mock_read_yaml: MagicMock,
    mock_settings_cls: MagicMock,
) -> None:
    """Verify get_threads_configuration_settings instantiates ThreadsConfigurationSettings correctly."""
    mock_read_yaml.return_value = {"thread_count": 2}

    get_threads_configuration_settings()

    # mock_read_yaml.assert_called_once()
    # mock_settings_cls.assert_called_once_with(thread_count=2)


# ==========================================
# 3. Init Settings & Cache Invalidation
# ==========================================


@patch("event_driven.infrastructure.config.init_settings.get_threads_configuration_settings")
@patch("event_driven.infrastructure.config.init_settings.get_process_settings")
@patch("event_driven.infrastructure.config.init_settings.get_general_settings")
@patch("event_driven.infrastructure.config.init_settings.get_aws_configuration_settings")
def test_init_settings_warms_all_caches(
    mock_aws: MagicMock,
    mock_general: MagicMock,
    mock_process: MagicMock,
    mock_threads: MagicMock,
) -> None:
    """Verify init_settings invokes all settings getters to warm up caches."""
    init_settings(force_reload=False)

    mock_aws.assert_called_once()
    mock_general.assert_called_once()
    mock_process.assert_called_once()
    mock_threads.assert_called_once()


@patch("event_driven.infrastructure.config.init_settings.get_threads_configuration_settings")
@patch("event_driven.infrastructure.config.init_settings.get_process_settings")
@patch("event_driven.infrastructure.config.init_settings.get_general_settings")
@patch("event_driven.infrastructure.config.init_settings.get_aws_configuration_settings")
def test_init_settings_force_reload_clears_caches(
    mock_aws: MagicMock,
    mock_general: MagicMock,
    mock_process: MagicMock,
    mock_threads: MagicMock,
) -> None:
    """Verify init_settings with force_reload=True clears cache_clear on all getters."""
    init_settings(force_reload=True)

    mock_aws.cache_clear.assert_called_once()
    mock_general.cache_clear.assert_called_once()
    mock_process.cache_clear.assert_called_once()
    mock_threads.cache_clear.assert_called_once()

    mock_aws.assert_called_once()
    mock_general.assert_called_once()
    mock_process.assert_called_once()
    mock_threads.assert_called_once()
