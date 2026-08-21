import logging
import time

from src.event_driven.infrastructure.threads.thread_base import BaseWorkerThread

# Configure logger
logger = logging.getLogger(__name__)


class ThreadManager:
    """Manager class responsible for orchestrating the lifecycle (startup,
    monitoring, graceful shutdown, and retry/recovery policy) of multiple worker threads.
    """

    def __init__(
        self, threads: list[BaseWorkerThread] | None = None, max_retries: int = 3, check_interval: float = 5.0
    ) -> None:
        """Initialize the ThreadManager.

        :param threads: Initial list of BaseWorkerThread instances to manage.
        :param max_retries: Maximum number of allowed failures per thread before triggering a full shutdown.
        :param check_interval: Time in seconds between health checks.
        """
        self._threads: list[BaseWorkerThread] = threads or []

        # Track metadata for recreation and failure counting
        self._thread_classes: dict[str, type[BaseWorkerThread]] = {}
        self._thread_init_args: dict[str, tuple] = {}
        self._thread_init_kwargs: dict[str, dict] = {}
        self._failure_counts: dict[str, int] = {}

        self.max_retries = max_retries
        self.check_interval = check_interval
        self._is_monitoring = False

        # Register any threads passed during initialization
        for thread in self._threads:
            self._register_thread_metadata(thread)

    def _register_thread_metadata(self, thread: BaseWorkerThread, *args, **kwargs) -> None:
        """Helper to store thread blueprint data for future restarts."""
        name = thread.name
        thread_cls = type(thread)
        self._thread_classes[name] = thread_cls or type(thread)
        self._thread_init_args[name] = args
        self._thread_init_kwargs[name] = kwargs
        if name not in self._failure_counts:
            self._failure_counts[name] = 0

    def add_thread(self, thread: BaseWorkerThread, *args, **kwargs) -> None:
        """Add a worker thread to the manager pool and cache its configuration.

        :param thread: An instance of a class inheriting from BaseWorkerThread.
        :param args: Positional arguments used to instantiate the thread.
        :param kwargs: Keyword arguments used to instantiate the thread.
        """
        self._threads.append(thread)
        self._register_thread_metadata(thread, *args, **kwargs)
        logger.info(f"Thread '{thread.name}' added to ThreadManager pool.")

    def start_all(self) -> None:
        """Start all registered worker threads concurrently."""
        logger.info(f"Starting {len(self._threads)} worker threads...")
        for thread in self._threads:
            if not thread.is_alive():
                thread.start()
                logger.info(f"Thread '{thread.name}' successfully launched.")
            else:
                logger.warning(f"Thread '{thread.name}' is already running.")

    def join_all(self, timeout: float | None = None) -> None:
        """Wait for all worker threads to finish their execution.

        :param timeout: Optional timeout in seconds to wait for threads to join.
        """
        logger.info("Waiting for all worker threads to complete...")
        for thread in self._threads:
            if thread.is_alive():
                thread.join(timeout=timeout)

    def stop_all(self, timeout_per_thread: float = 2.0) -> None:
        """Signal all threads to stop gracefully, wait for them to finish,
        and handle timeouts.

        :param timeout_per_thread: Time in seconds to wait for each thread to shut down.
        """
        self._is_monitoring = False
        logger.info("Initiating graceful shutdown for all worker threads...")

        # 1. Trigger the stop flag on all threads
        for thread in self._threads:
            logger.info(f"Sending stop signal to thread '{thread.name}'...")
            thread.stop()

        # 2. Wait for each thread to terminate gracefully
        for thread in self._threads:
            if thread.is_alive():
                thread.join(timeout=timeout_per_thread)
                if thread.is_alive():
                    logger.warning(f"Thread '{thread.name}' did not terminate gracefully within the timeout period.")
                else:
                    logger.info(f"Thread '{thread.name}' stopped successfully.")

        logger.info("All worker threads have been shut down.")

    def monitor_health(self) -> dict[str, bool]:
        """Check the active status of all managed threads.

        :return: A dictionary mapping thread names to their alive status (True/False).
        """
        health_status = {}
        for thread in self._threads:
            health_status[thread.name] = thread.is_alive()
        return health_status

    def start_monitoring(self) -> None:
        """Continuously monitor thread health. If a thread dies unexpectedly, attempt to restart it.
        If it exceeds `max_retries` failures, aborts and shuts down the entire manager.
        """
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

                    # Recreate and restart the thread
                    try:
                        cls = self._thread_classes[name]
                        args = self._thread_init_args[name]
                        kwargs = self._thread_init_kwargs[name]

                        logger.info(f"Attempting to restart thread '{name}'...")
                        new_thread = cls(*args, **kwargs)
                        new_thread.start()

                        # Replace old dead thread reference with the new instance
                        self._threads[i] = new_thread
                        logger.info(f"Thread '{name}' successfully restarted.")

                    except Exception as e:
                        logger.critical(f"Failed to restart thread '{name}': {e}")
                        self.stop_all()
                        return
