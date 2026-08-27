# domain/use_cases/process_notification.py
from logging import getLogger
from typing import Optional

from event_driven.domain.ports import BasePort
from event_driven.domain.schemas import NotificationModel

logger = getLogger(__name__)


class NotificationUseCase:
    """Domain logic - process and dispatch user notifications."""

    def __init__(self, adapter: BasePort | None = None) -> None:
        self._adapter = adapter  # Accepts ANY object implementing BasePort

    def execute(self, payload: NotificationModel) -> Optional[NotificationModel]:
        # Validaciones de lógica de negocio
        if not payload.notification_id:
            raise ValueError("Notification must contain a valid notification_id.")
        if not payload.recipient:
            raise ValueError("Notification recipient cannot be empty.")

        try:
            # Registrar el procesamiento y mostrar parte del contenido en el log
            logger.info(
                f"Sending Notification [ID: {payload.notification_id}] | "
                f"Order: {payload.order_id} | "
                f"Channel: {payload.channel} | "
                f"To: {payload.recipient} | "
                f"Subject: '{payload.subject}' | "
                f"Body Preview: '{payload.message[:50]}...'"
            )

            # Envío real de la notificación a través del adaptador (ej. Email, SMS, Push)
            if self._adapter:
                self._adapter.send(payload)

            # Marcar como enviada si el proceso fue exitoso
            payload.status = "SENT"
            logger.info(f"Notification {payload.notification_id} dispatched successfully.")

            return payload

        except Exception as e:
            logger.error(f"Error processing notification {payload.notification_id} for order {payload.order_id}: {e}")
            raise e