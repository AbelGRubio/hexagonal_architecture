import signal
import sys
import time
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel

from event_driven.infrastructure.config.enumerations import BrokersEnum, ThreadsEnum
from event_driven.infrastructure.messaging.broker_factory import MessageBrokerFactory
from event_driven.infrastructure.messaging.brokers import IMessageBroker
from event_driven.infrastructure.threads import InventoryThread, ThreadManager, ProducerThread
from event_driven.logger import get_logger, propagate_loggers
from event_driven.infrastructure.config.resolved import ThreadsConfigurations

logger = get_logger(__name__)


def main() -> None:
    logger.info("Initializing Event-Driven Architecture Application...")

    # 1. Instantiate the Thread Manager
    # (max_retries=3 is default, meaning it will retry up to 3 times per thread)
    manager = ThreadManager(max_retries=3, check_interval=5.0)
    path = Path("pymodeller/threads.yaml")

    if path.exists():
        with open(path, "r", encoding="utf-8") as file:
            raw_data: dict[str, Any] = yaml.safe_load(file) or {}

        # Carga automática limpia en una sola línea
        config = ThreadsConfigurations.model_validate(raw_data)
    f = 1
    # 2. Register worker threads
    # Now we pass:
    #   - An initial instance of the thread
    #   - The class itself (InventoryThread / OrderServiceThread)
    #   - The keyword arguments needed to re-instantiate it if it fails
    manager.add_thread(ProducerThread, config=config.get_thread_config(thread_name=ThreadsEnum.PRODUCER))
    manager.add_thread(InventoryThread, config=config.get_thread_config(thread_name=ThreadsEnum.INVENTORY))

    # manager.add_thread(OrderThread, broker=message_broker)

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


propagate_loggers()

if __name__ == "__main__":
    main()
