"""AUTO-GENERATED SETTINGS MANAGER."""
# YAML-SHA256: 4ecb462fff68cab657f27b8f19ad412e317365f222a163b66ab2d0c992cb4170

from functools import lru_cache
from pathlib import Path

import yaml

from event_driven.infrastructure.config.settings import (
    AwsConfigurationSettings,
    GeneralSettings,
    ProcessSettings,
    ThreadsConfigurationSettings,
)


def _read_yaml(config_path: Path) -> dict:
    """Read YAML file safely."""
    if not config_path.is_file():
        return {}
    with open(config_path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


@lru_cache(maxsize=1)
def get_aws_configuration_settings(path: Path | None = None) -> AwsConfigurationSettings:
    """Return the cached application settings instance for AwsConfigurationSettings.

    Source: None.
    """
    # Single file loading
    path = path if path else Path("None")
    values = _read_yaml(path)
    return AwsConfigurationSettings(**values)


@lru_cache(maxsize=1)
def get_general_settings(path: Path | None = None) -> GeneralSettings:
    """Return the cached application settings instance for GeneralSettings.

    Source: None.
    """
    # Single file loading
    path = path if path else Path("None")
    values = _read_yaml(path)
    return GeneralSettings(**values)


@lru_cache(maxsize=1)
def get_process_settings(path: Path | None = None) -> ProcessSettings:
    """Return the cached application settings instance for ProcessSettings.

    Source: None.
    """
    # Single file loading
    path = path if path else Path("None")
    values = _read_yaml(path)
    return ProcessSettings(**values)


@lru_cache(maxsize=1)
def get_threads_configuration_settings(path: Path | None = None) -> ThreadsConfigurationSettings:
    """Return the cached application settings instance for ThreadsConfigurationSettings.

    Source: None.
    """
    # Single file loading
    path = path if path else Path("None")
    values = _read_yaml(path)
    return ThreadsConfigurationSettings(**values)


def init_settings(force_reload: bool = False) -> None:
    """Initialize all settings.

    If force_reload is True, clears the lru_cache for each getter.
    """
    if force_reload:
        get_aws_configuration_settings.cache_clear()
        get_general_settings.cache_clear()
        get_process_settings.cache_clear()
        get_threads_configuration_settings.cache_clear()

    # Initialize / Warm up cache
    get_aws_configuration_settings()
    get_general_settings()
    get_process_settings()
    get_threads_configuration_settings()
