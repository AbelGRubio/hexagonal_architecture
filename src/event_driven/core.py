import signal
import sys

from event_driven.infrastructure.config.enumerations import ThreadsEnum
from event_driven.infrastructure.config.init_resolved import get_threads_configurations
from event_driven.infrastructure.threads import (
    ProducerThread,
    ThreadManager, InventoryThread, OrderThread, PaymentThread, NotificationThread, ErrorThread
)
from event_driven.logger import get_logger

logger = get_logger(__name__)


def main() -> None:
    logger.info("Initializing Event-Driven Architecture Application...")

    # 1. Instantiate the Thread Manager
    # (max_retries=3 is default, meaning it will retry up to 3 times per thread)
    manager = ThreadManager(max_retries=3, check_interval=5.0)
    config = get_threads_configurations()

    # 2. Register worker threads
    # Now we pass:
    #   - An initial instance of the thread
    #   - The class itself (InventoryThread / OrderServiceThread)
    #   - The keyword arguments needed to re-instantiate it if it fails
    manager.add_thread(ProducerThread, config=config.get_thread_config(thread_name=ThreadsEnum.PRODUCER))
    manager.add_thread(InventoryThread, config=config.get_thread_config(thread_name=ThreadsEnum.INVENTORY))
    manager.add_thread(OrderThread, config=config.get_thread_config(thread_name=ThreadsEnum.ORDER))
    manager.add_thread(PaymentThread, config=config.get_thread_config(thread_name=ThreadsEnum.PAYMENT))
    manager.add_thread(NotificationThread, config=config.get_thread_config(thread_name=ThreadsEnum.NOTIFICATION))
    manager.add_thread(ErrorThread, config=config.get_thread_config(thread_name=ThreadsEnum.ERROR))

    # 3. Define graceful shutdown handler for signals (SIGINT / SIGTERM)
    def shutdown_handler(signum, frame) -> None:
        logger.info("Termination signal received. Shutting down application gracefully...")
        manager.stop_all()
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown_handler)
    signal.signal(signal.SIGTERM, shutdown_handler)

    # 4. Start all infrastructure worker threads
    manager.start_all()

    # 5. Start the built-in health monitoring loop
    # (This replaces the manual while True loop, checks thread status,
    # handles restarts, and shuts down if max retries are exceeded)
    logger.info("Application is running. Health monitoring active. Press Ctrl+C to exit.")
    try:
        manager.start_monitoring()
    except KeyboardInterrupt:
        shutdown_handler(None, None)

    logger.info("Application ended")
