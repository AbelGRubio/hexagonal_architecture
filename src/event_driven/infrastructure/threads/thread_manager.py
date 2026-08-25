"""Thread manager for supervising worker lifecycle and restart behavior.

This module coordinates the startup, health checks, and graceful termination of
multiple worker threads in a centralized manager.
"""

import logging
import time

from event_driven.infrastructure.threads.thread_base_old import BaseWorkerThread

logger = logging.getLogger(__name__)


class ThreadManager:
    """Manage a pool of worker threads and their restart policy."""

    def __init__(
        self,
        threads: list[BaseWorkerThread] | None = None,
        max_retries: int = 3,
        check_interval: float = 5.0,
    ) -> None:
        """Initialize the manager with an optional initial set of threads."""
        self._threads: list[BaseWorkerThread] = threads or []

        self._thread_classes: dict[str, type[BaseWorkerThread]] = {}
        self._thread_init_args: dict[str, tuple[object, ...]] = {}
        self._thread_init_kwargs: dict[str, dict[str, object]] = {}
        self._failure_counts: dict[str, int] = {}

        self.max_retries = max_retries
        self.check_interval = check_interval
        self._is_monitoring = False

        for thread in self._threads:
            self._register_thread_metadata(thread)

    def _register_thread_metadata(self, thread: BaseWorkerThread, *args: object, **kwargs: object) -> None:
        """Store metadata needed to recreate a worker if it stops unexpectedly."""
        name = thread.name
        thread_cls = type(thread)
        self._thread_classes[name] = thread_cls or type(thread)
        self._thread_init_args[name] = args
        self._thread_init_kwargs[name] = kwargs
        if name not in self._failure_counts:
            self._failure_counts[name] = 0

    def add_thread(self, thread: type[BaseWorkerThread], *args: object, **kwargs: object) -> None:
        """Create and register a worker instance in the managed pool."""
        th = thread(**kwargs)
        self._threads.append(th)
        self._register_thread_metadata(th, *args, **kwargs)
        logger.info(f"Thread '{th.name}' added to ThreadManager pool.")

    def start_all(self) -> None:
        """Start every managed thread that is not already running."""
        logger.info(f"Starting {len(self._threads)} worker threads...")
        for thread in self._threads:
            if not thread.is_alive():
                thread.start()
                logger.info(f"Thread '{thread.name}' successfully launched.")
            else:
                logger.warning(f"Thread '{thread.name}' is already running.")

    def join_all(self, timeout: float | None = None) -> None:
        """Wait for all registered threads to finish, optionally respecting a timeout."""
        logger.info("Waiting for all worker threads to complete...")
        for thread in self._threads:
            if thread.is_alive():
                thread.join(timeout=timeout)

    def stop_all(self, timeout_per_thread: float = 4.0) -> None:
        """Signal each worker to exit gracefully and then wait for shutdown completion."""
        self._is_monitoring = False
        logger.info("Initiating graceful shutdown for all worker threads...")

        for thread in self._threads:
            logger.info(f"Sending stop signal to thread '{thread.name}'...")
            thread.stop()

        for thread in self._threads:
            if thread.is_alive():
                thread.join(timeout=timeout_per_thread)
                if thread.is_alive():
                    logger.warning(f"Thread '{thread.name}' did not terminate gracefully within the timeout period.")
                else:
                    logger.info(f"Thread '{thread.name}' stopped successfully.")

        logger.info("All worker threads have been shut down.")

    def monitor_health(self) -> dict[str, bool]:
        """Return the alive status of every managed worker."""
        health_status: dict[str, bool] = {}
        for thread in self._threads:
            health_status[thread.name] = thread.is_alive()
        return health_status

    def start_monitoring(self) -> None:
        """Continuously monitor threads and restart any that exit unexpectedly."""
        self._is_monitoring = True
        logger.info(f"Health monitor started (max_retries={self.max_retries}).")

        while self._is_monitoring:
            time.sleep(self.check_interval)

            if not self._is_monitoring:
                break

            for i, thread in enumerate(list(self._threads)):
                if not thread.is_alive():
                    name = thread.name
                    self._failure_counts[name] += 1
                    failures = self._failure_counts[name]

                    logger.error(
                        f"Thread '{name}' has stopped unexpectedly! (Failure count: {failures}/{self.max_retries})"
                    )

                    if failures > self.max_retries:
                        logger.critical(
                            f"Thread '{name}' exceeded max retries ({self.max_retries}). "
                            "Shutting down application due to persistent thread failure."
                        )
                        self.stop_all()
                        return

                    try:
                        cls = self._thread_classes[name]
                        args = self._thread_init_args[name]
                        kwargs = self._thread_init_kwargs[name]

                        logger.info(f"Attempting to restart thread '{name}'...")
                        new_thread = cls(*args, **kwargs)
                        new_thread.start()

                        self._threads[i] = new_thread
                        logger.info(f"Thread '{name}' successfully restarted.")

                    except Exception as exc:
                        logger.critical(f"Failed to restart thread '{name}': {exc}")
                        self.stop_all()
                        return
