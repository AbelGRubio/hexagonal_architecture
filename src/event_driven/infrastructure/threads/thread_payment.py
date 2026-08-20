import queue
from typing import Any, Optional

from pydantic import BaseModel, ValidationError

from .thread_base import BaseWorkerThread
from event_driven.infrastructure.messaging.brokers.interface_message import IMessageBroker
from event_driven.logger import get_logger


logger = get_logger(__name__)


class PaymentServiceThread(BaseWorkerThread[BaseModel, BaseModel]):
    """
    Consumer thread for the Payment Service using the integrated message broker.
    Processes financial transactions for orders.
    """

    def __init__(
            self,
            broker: IMessageBroker,
            consume_topic: str = "inventory-reserved",
            publish_topic: Optional[str] = "payment-processed",
            name: str = "PaymentService"
    ):
        super().__init__(
            payload_model=BaseModel,  # Reemplaza con tu modelo real
            broker=broker,
            consume_destination=consume_topic,
            publish_destination=publish_topic,
            name=name
        )

    def process_payload(self, payload: BaseModel) -> Optional[BaseModel]:
        logger.info(f"[{self.name}] Processing payment...")

        # Lógica de negocio de pagos
        # PaymentBusinessLogic.charge(payload)

        return None

    def handle_validation_error(self, raw_message: Any, error: ValidationError) -> None:
        logger.error(f"[{self.name}] Validation error in payment data: {error}")

    def handle_processing_error(self, payload: BaseModel, error: Exception) -> None:
        logger.error(f"[{self.name}] Payment gateway failure: {error}")
