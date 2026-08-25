"""Inventory worker thread implementation."""

import logging

from event_driven.domain.schemas.cart_item import CartItemModel
from event_driven.domain.schemas.order_created import OrderCreatedModel
from event_driven.infrastructure.messaging.brokers.interface_message import IMessageBroker

from .thread_base import BaseWorkerThread

logger = logging.getLogger(__name__)


class InventoryThread(BaseWorkerThread[CartItemModel, OrderCreatedModel]):
    """Worker that processes inventory-related cart item messages."""

    def __init__(
        self,
        broker: IMessageBroker,
        consume_topic: str = "cart-items",
        publish_topic: str | None = "inventory-reserved",
        name: str = "InventoryThread",
    ) -> None:
        """Initialize the inventory worker with its message destinations."""
        super().__init__(
            payload_model=CartItemModel,
            broker=broker,
            consume_destination=consume_topic,
            publish_destination=publish_topic,
            name=name,
        )

    def process_payload(self, payload: CartItemModel) -> OrderCreatedModel | None:
        """Process an inventory item and optionally emit an output event."""
        logger.info(
            f"[{self.name}] Processing inventory for item ID: {payload.id if hasattr(payload, 'id') else 'unknown'}"
        )

        return None
