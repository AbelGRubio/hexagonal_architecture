import logging
from typing import Any, Optional
from pydantic import ValidationError

from .thread_base import BaseWorkerThread
from event_driven.domain.schemas.cart_item import CartItemModel
from event_driven.domain.schemas.order_created import OrderCreatedModel
from event_driven.infrastructure.messaging.brokers.interface_message import IMessageBroker

logger = logging.getLogger(__name__)


class InventoryThread(BaseWorkerThread[CartItemModel, OrderCreatedModel]):
    """
    Consumer thread for the Inventory Service using the integrated broker in BaseWorkerThread.
    """

    def __init__(
            self,
            broker: IMessageBroker,
            consume_topic: str = "cart-items",
            publish_topic: Optional[str] = "order-created",
            name: str = "InventoryService-Thread"
    ):
        super().__init__(
            payload_model=CartItemModel,
            broker=broker,
            consume_destination=consume_topic,
            publish_destination=publish_topic,
            name=name
        )

    def process_payload(self, payload: CartItemModel) -> Optional[OrderCreatedModel]:
        logger.info(f"[{self.name}] Processing inventory for item ID: "
                    f"{payload.id if hasattr(payload, 'id') else 'unknown'}")

        # --- TUS REGLAS DE NEGOCIO ---
        # InventoryBusinessLogic.execute(payload)

        # Si quieres enviar un mensaje de salida, simplemente retórnalo.
        # La clase base BaseWorkerThread se encargará de enviarlo automáticamente a publish_destination.
        # return OrderCreatedModel(...)
        return None

    def handle_validation_error(self, raw_message: Any, error: ValidationError) -> None:
        logger.error(f"[{self.name}] Validation error: {error}")
        # Opcional: podrías usar self.broker.publish("dlq-topic", str(raw_message)) si deseas enviar a una DLQ

    def handle_processing_error(self, payload: CartItemModel, error: Exception) -> None:
        logger.error(f"[{self.name}] Runtime processing error: {error}")