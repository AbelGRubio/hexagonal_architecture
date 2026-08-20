import logging
from typing import Any, Optional
from pydantic import ValidationError, BaseModel

from .thread_base import BaseWorkerThread
from event_driven.domain.schemas.notification import NotificationModel  # Ejemplo de tu modelo
from event_driven.infrastructure.messaging.brokers.interface_message import IMessageBroker

logger = logging.getLogger(__name__)


class NotificationServiceThread(BaseWorkerThread[NotificationModel, BaseModel]):
    """
    Consumer thread for the Notification Service using the integrated message broker.
    Sends emails or final alerts to the client.
    """

    def __init__(
            self,
            broker: IMessageBroker,
            consume_topic: str = "notifications-topic",
            name: str = "NotificationService-Thread"
    ):
        super().__init__(
            payload_model=NotificationModel,
            broker=broker,
            consume_destination=consume_topic,
            publish_destination=None,  # Al ser el último paso, no requiere publicar hacia adelante
            name=name
        )

    def process_payload(self, payload: NotificationModel) -> Optional[BaseModel]:
        logger.info(f"[{self.name}] Sending notification to user...")

        # --- TUS REGLAS DE NEGOCIO ---
        # NotificationBusinessLogic.send_email(payload)

        return None

    def handle_validation_error(self, raw_message: Any, error: ValidationError) -> None:
        logger.error(f"[{self.name}] Validation error in notification: {error}")

    def handle_processing_error(self, payload: NotificationModel, error: Exception) -> None:
        logger.error(f"[{self.name}] Runtime error sending notification: {error}")