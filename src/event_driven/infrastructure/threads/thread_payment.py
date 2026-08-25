"""Payment worker thread implementation."""

from pydantic import BaseModel

from event_driven.infrastructure.messaging.brokers.interface_message import IMessageBroker
from event_driven.logger import get_logger

from .thread_base_old import BaseWorkerThread

logger = get_logger(__name__)


class PaymentThread(BaseWorkerThread[BaseModel, BaseModel]):
    """Worker responsible for processing payment-related events."""

    def __init__(
        self,
        broker: IMessageBroker,
        consume_topic: str = "inventory-reserved",
        publish_topic: str | None = "payment-processed",
        name: str = "PaymentThread",
    ) -> None:
        """Initialize the payment worker and link it to its message destinations."""
        super().__init__(
            payload_model=BaseModel,
            broker=broker,
            consume_destination=consume_topic,
            publish_destination=publish_topic,
            name=name,
        )

    def process_payload(self, payload: BaseModel) -> BaseModel | None:
        """Process a validated payment payload."""
        logger.info(f"[{self.name}] Processing payment...")
        return None
