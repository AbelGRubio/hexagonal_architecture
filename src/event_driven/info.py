"""Info package."""

from __future__ import annotations

import platform
import sys
import time
from collections.abc import Callable
from importlib.metadata import distributions
from pathlib import Path
from typing import Any, TypeVar

import cpuinfo
import psutil

from event_driven.logger import get_logger

F = TypeVar("F", bound=Callable[..., Any])
logger = get_logger(__name__)

# Cached installed packages
INSTALLED_PACKAGES = {dist.metadata["Name"]: dist.version for dist in distributions()}

# Default modules to log
DEFAULT_MODULES = ["httpx"]


def info_os() -> None:
    """Log operating system version and architecture."""
    logger.info(f"{'OS':<25}{platform.platform()}")


def info_software(modules: list[str] | None = None) -> None:
    """Log Python version and versions of specified modules.

    Args:
        modules (list[str] | None): List of module names to log. If None, uses DEFAULT_MODULES.
    """
    logger.info(f"{'ENV':<25}{sys.prefix}")
    logger.info(f"{'PYTHON':<25}{platform.python_version()}")

    for module in modules or DEFAULT_MODULES:
        version = INSTALLED_PACKAGES.get(module, "N/A")
        logger.info(f" - {module:<22}{version}")


def info_hardware() -> None:
    """Log CPU model, core count, and RAM size."""
    cpu = cpuinfo.get_cpu_info().get("brand_raw", "Unknown CPU")
    cores = psutil.cpu_count(logical=True)
    ram_gb = round(psutil.virtual_memory().total / (1024**3))
    logger.info(f"{'MACHINE':<25}{cpu} ({cores} cores, {ram_gb} GB RAM)")


def info_system(modules: list[str] | None = None) -> None:
    """Log full system information including OS, hardware, and software.

    Args:
        modules (list[str] | None): List of module names to log versions for. Defaults to DEFAULT_MODULES.
    """
    info_hardware()
    info_os()
    info_software(modules)
    logger.info(f"{'EXECUTION PATH':<25}{Path().absolute()}")
    logger.info(f"{'EXECUTION DATE':<25}{time.ctime()}")


def get_memory_usage(obj: object) -> float:
    """Calculate and return memory usage of an object in megabytes.

    Note: This function uses `sys.getsizeof`, which only accounts for the memory
    usage of the object itself, not including referenced objects. For a more
    accurate measurement, consider using a library like `pympler`.

    Args:
        obj (object): The object to analyze.

    Returns:
        float: Approximate memory usage in MB.
    """
    return round(sys.getsizeof(obj) / 1024**2, 3)
