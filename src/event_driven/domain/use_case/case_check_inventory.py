# domain/use_cases/process_order.py
from typing import Optional
import uuid
from event_driven.domain.ports import BasePort
from event_driven.domain.schemas import CartItemsModel, OrderCreatedModel
from logging import getLogger
from datetime import datetime
logger = getLogger(__name__)


class CheckInventoryUseCase:
    """Domain logic - only depends on the Port abstraction."""

    def __init__(self, adapter: BasePort) -> None:
        self._adapter = adapter  # Accepts ANY object implementing BasePort

    def execute(self, payload: CartItemsModel) -> Optional[OrderCreatedModel]:
        # Business logic validation
        if not payload.items:
            raise ValueError("Order must contain at least one item.")

        try:
            logger.info(f"Checking inventory use case order: {payload.id}")
            # Save to DB via the Port (abstract interface)
            # self._adapter.save(payload)
            order = OrderCreatedModel(
                event_id=payload.id,
                order_id=str(uuid.uuid4()),
                user_id=str(uuid.uuid4()),
                timestamp=datetime.now(),
                items=payload.items,
            )
            return order
        except Exception as e:
            logger.error(e)

        return None