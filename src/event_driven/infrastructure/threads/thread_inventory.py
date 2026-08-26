"""Inventory worker thread implementation."""

import logging
from typing import Optional

from event_driven.domain.schemas import CartItemsModel, OrderCreatedModel
from event_driven.infrastructure.config.schemas import ThreadConfigModel, BrokerConfigModel
from event_driven.infrastructure.config.enumerations import BrokersEnum, ThreadsEnum

from .thread_base import BaseWorkerThread

logger = logging.getLogger(__name__)


class InventoryThread(BaseWorkerThread[CartItemsModel, OrderCreatedModel]):
    """Worker that processes inventory-related cart item messages."""

    def __init__(
        self,
        config: ThreadConfigModel,
    ) -> None:
        """Initialize the inventory worker with configuration and broker factory.

        Args:
            config: Thread configuration model containing brokers and destinations.
        """
        super().__init__(
            config=config,
            payload_model=CartItemsModel,
        )

    def process_payload(self, payload: CartItemsModel) -> Optional[OrderCreatedModel]:
        """Process an inventory item and optionally emit an output event."""
        logger.info(
            f"Processing inventory for item ID: {payload.id if hasattr(payload, 'id') else 'unknown'}"
        )

        return None
