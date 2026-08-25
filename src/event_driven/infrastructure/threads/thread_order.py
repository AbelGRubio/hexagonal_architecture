"""Order worker thread implementation."""

from pydantic import BaseModel

from event_driven.infrastructure.messaging.brokers.interface_message import IMessageBroker
from event_driven.logger import get_logger

from .thread_base import BaseWorkerThread

logger = get_logger(__name__)


class OrderThread(BaseWorkerThread[BaseModel, BaseModel]):
    """Worker that processes order creation or order-related events."""

    def __init__(
        self,
        broker: IMessageBroker,
        consume_topic: str = "payment-processed",
        publish_topic: str | None = "orders-created",
        name: str = "OrderThread",
    ) -> None:
        """Initialize the order worker with its input and output message topics."""
        super().__init__(
            payload_model=BaseModel,
            broker=broker,
            consume_destination=consume_topic,
            publish_destination=publish_topic,
            name=name,
        )

    def process_payload(self, payload: BaseModel) -> BaseModel | None:
        """Process a validated order payload."""
        logger.info(f"[{self.name}] Processing order: {payload}")
        return None
