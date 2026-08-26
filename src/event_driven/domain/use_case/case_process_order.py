# domain/use_cases/process_order.py

from event_driven.domain.ports import BasePort
from event_driven.domain.schemas.order_created import OrderCreatedModel
from logging import getLogger

logger = getLogger(__name__)


class ProcessOrderUseCase:
    """Domain logic - only depends on the Port abstraction."""

    def __init__(self, adapter: BasePort) -> None:
        self._adapter = adapter  # Accepts ANY object implementing BasePort

    def execute(self, payload: OrderCreatedModel) -> None:
        # Business logic validation
        if not payload.items:
            raise ValueError("Order must contain at least one item.")

        try:
            logger.info(f"Processing use case order: {payload.order_id}")
            # Save to DB via the Port (abstract interface)
            # self._adapter.save(payload)
        except Exception as e:
            logger.error(e)
