"""AUTO-GENERATED SETTINGS MANAGER."""

from functools import lru_cache
from pathlib import Path
from typing import Optional

import yaml

from event_driven.infrastructure.config.resolved import ThreadsConfigurations


def _read_yaml(config_path: Path) -> dict:
    """Read YAML file safely."""
    if not config_path.is_file():
        return {}
    with open(config_path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


@lru_cache(maxsize=1)
def get_threads_configurations(path: Optional[Path] = Path("pymodeller/threads.yaml")) -> ThreadsConfigurations:
    """Return the cached application settings instance for AwsConfigurationSettings.

    Source: None.
    """
    # Single file loading
    path = path if path else Path("threads.yaml")
    values = _read_yaml(path)
    return ThreadsConfigurations(**values)


def init_resolved(force_reload: bool = False) -> None:
    """Initialize all settings.

    If force_reload is True, clears the lru_cache for each getter.
    """
    if force_reload:
        get_threads_configurations.cache_clear()

    # Initialize / Warm up cache
    get_threads_configurations()
