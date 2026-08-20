import logging
from typing import Any, Optional
from pydantic import BaseModel, ValidationError

from .thread_base import BaseWorkerThread
from event_driven.infrastructure.messaging.brokers.interface_message import IMessageBroker
from event_driven.logger import get_logger
logger = get_logger(__name__)


class OrderServiceThread(BaseWorkerThread[BaseModel, BaseModel]):
    """
    Consumer thread for the Order Service using the integrated message broker.
    Listens for order creation events or initial requests.
    """

    def __init__(
            self,
            broker: IMessageBroker,
            consume_topic: str = "orders-incoming",
            publish_topic: Optional[str] = "orders-created",
            name: str = "OrderService-Thread"
    ):
        super().__init__(
            payload_model=BaseModel,  # Reemplaza con tu modelo real, ej: OrderModel
            broker=broker,
            consume_destination=consume_topic,
            publish_destination=publish_topic,
            name=name
        )

    def process_payload(self, payload: BaseModel) -> Optional[BaseModel]:
        logger.info(f"[{self.name}] Processing order: {payload}")

        # 1. Llamar a la lógica de negocio pura
        # result = OrderBusinessLogic.process(payload)

        # Si retornas un objeto Pydantic, la clase base lo publicará automáticamente en publish_destination
        # return result
        return None

    def handle_validation_error(self, raw_message: Any, error: ValidationError) -> None:
        logger.error(f"[{self.name}] Validation error in order: {error}. Raw message: {raw_message}")

    def handle_processing_error(self, payload: BaseModel, error: Exception) -> None:
        logger.error(f"[{self.name}] Critical processing error in order: {error}")
