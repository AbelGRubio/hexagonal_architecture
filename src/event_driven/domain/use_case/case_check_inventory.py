# domain/use_cases/process_order.py

from event_driven.domain.ports import BasePort
from event_driven.domain.schemas import CartItemsModel
from logging import getLogger

logger = getLogger(__name__)


class CheckInventoryUseCase:
    """Domain logic - only depends on the Port abstraction."""

    def __init__(self, adapter: BasePort) -> None:
        self._adapter = adapter  # Accepts ANY object implementing BasePort

    def execute(self, payload: CartItemsModel) -> None:
        # Business logic validation
        if not payload.items:
            raise ValueError("Order must contain at least one item.")

        try:
            logger.info(f"---Checking inventory use case order: {payload.id}")
            # Save to DB via the Port (abstract interface)
            self._adapter.save(payload)
        except Exception as e:
            logger.error(e)
