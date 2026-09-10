# domain/use_cases/process_payment.py
import uuid
from datetime import datetime
from logging import getLogger

from event_driven.domain.ports import BasePort
from event_driven.domain.schemas import NotificationModel, PaymentModel

logger = getLogger(__name__)


class PaymentUseCase:
    """Domain logic - process payment and generate notification."""

    def __init__(self, adapter: BasePort | None = None) -> None:
        self._adapter = adapter  # Accepts ANY object implementing BasePort

    def execute(self, payload: PaymentModel) -> NotificationModel | None:
        # Business logic validation
        if payload.amount <= 0:
            raise ValueError("Payment amount must be greater than zero.")

        try:
            logger.info(f"Processing payment {payload.payment_id} for order: {payload.order_id}")

            # 1. Simular / procesar pago a través del adaptador si existe
            # if self._adapter:
            #     self._adapter.process_payment(payload)

            # 2. Definir asunto y mensaje según el estado del pago
            if payload.status == "SUCCESS":
                subject = f"Order #{payload.order_id} Confirmed!"
                message = f"Your payment of {payload.amount} {payload.currency} was processed successfully."
                notification_status = "PENDING"
            else:
                subject = f"Payment Failed for Order #{payload.order_id}"
                message = f"There was an issue processing your payment of {payload.amount} {payload.currency}."
                notification_status = "FAILED"

            # 3. Construir / transformar a NotificationModel
            notification = NotificationModel(
                event_id=f"evt_{uuid.uuid4().hex[:8]}",
                notification_id=f"notif_{uuid.uuid4().hex[:8]}",
                order_id=payload.order_id,
                user_id=payload.user_id,
                channel="EMAIL",
                recipient=f"user_{payload.user_id}@example.com" if payload.user_id else "customer@example.com",
                subject=subject,
                message=message,
                status=notification_status,
                timestamp=datetime.now(),
            )

            # 4. Enviar / Guardar notificación si aplica
            # if self._adapter:
            #     self._adapter.send_notification(notification)

            logger.info(f"Notification model created successfully for order {payload.order_id}")
            return notification

        except Exception as e:
            logger.error(f"Error processing payment notification for order {payload.order_id}: {e}")
            raise e
