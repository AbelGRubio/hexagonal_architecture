import signal
import sys

from event_driven.domain.schemas.cart_item import CartItemModel
from event_driven.domain.schemas.order_created import OrderCreatedModel
from event_driven.infrastructure.config.enum.brokers import Broker
from event_driven.infrastructure.messaging.broker_factory import MessageBrokerFactory
from event_driven.infrastructure.threads.thread_inventory import InventoryThread
from event_driven.infrastructure.threads.thread_manager import ThreadManager
from event_driven.infrastructure.threads.thread_order import OrderServiceThread
from event_driven.logger import get_logger

logger = get_logger(__name__)


def main() -> None:
    logger.info("Initializing Event-Driven Architecture Application...")

    # 1. Instantiate the Thread Manager
    # (max_retries=3 is default, meaning it will retry up to 3 times per thread)
    manager = ThreadManager(max_retries=3, check_interval=5.0)

    # 2. Register worker threads
    # Now we pass:
    #   - An initial instance of the thread
    #   - The class itself (InventoryThread / OrderServiceThread)
    #   - The keyword arguments needed to re-instantiate it if it fails
    manager.add_thread(
        InventoryThread(
            schema_model=CartItemModel,
            name="Inventory-Worker"
        )
    )

    manager.add_thread(
        OrderServiceThread(
            schema_model=OrderCreatedModel,
            name="Order-Worker"
        )
    )

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


if __name__ == '__main__':
    logger.info("Hola")
    message_broker = MessageBrokerFactory.create_broker(Broker.KAFKA)
    logger.info("Broker created")

    # Run the main application
    # main()