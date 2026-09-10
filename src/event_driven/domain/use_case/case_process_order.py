# domain/use_cases/process_order.py
import uuid
from datetime import datetime
from logging import getLogger

from event_driven.domain.ports import BasePort
from event_driven.domain.schemas import OrderCreatedModel, PaymentModel

logger = getLogger(__name__)


class ProcessOrderUseCase:
    """Domain logic - only depends on the Port abstraction."""

    def __init__(self, adapter: BasePort) -> None:
        self._adapter = adapter  # Accepts ANY object implementing BasePort

    def execute(self, payload: OrderCreatedModel) -> PaymentModel | None:
        # Business logic validation
        if not payload.items:
            raise ValueError("Order must contain at least one item.")

        try:
            logger.info(f"Processing use case order: {payload.order_id}")

            # 1. Calcular el monto total acumulado de todos los ítems del pedido
            total_amount = sum((item.unit_price or 0.0) * (item.quantity or 1) for item in payload.items)

            # 2. Construir/transformar el modelo de PaymentModel
            payment = PaymentModel(
                event_id=f"evt_{uuid.uuid4().hex[:8]}",
                payment_id=f"pay_{uuid.uuid4().hex[:8]}",
                order_id=payload.order_id,
                user_id=payload.user_id,
                amount=round(total_amount, 2),
                currency="EUR",
                status="PENDING",
                payment_method="CREDIT_CARD",
                timestamp=datetime.now(),
            )

            # 3. Guardar o procesar a través del Puerto / Adaptador
            # self._adapter.save(payment)

            logger.info(f"Payment model created successfully for order {payload.order_id} with total: {payment.amount}")
            return payment

        except Exception as e:
            logger.error(f"Error processing order {payload.order_id}: {e}")
            raise e
