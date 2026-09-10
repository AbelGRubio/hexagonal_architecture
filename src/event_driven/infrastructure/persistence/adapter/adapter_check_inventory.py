"""Inventory check persistence adapter.

========================================================================================================================
Name:         src/event_driven/infrastructure/persistence/adapter/adapter_check_inventory.py
Description:  Persistence adapter that stores and retrieves order inventory records with Peewee.
Author:       PyModeller
Status:       Development
Copyright ©2026. All rights reserved.
========================================================================================================================
"""

from logging import getLogger

from event_driven.domain.ports import BasePort
from event_driven.domain.schemas import OrderCreatedModel
from event_driven.infrastructure.persistence.models import OrderCreated

logger = getLogger(__name__)


class AdapterCheckInventory(BasePort):
    """Concrete Peewee ORM adapter for inventory-order persistence."""

    def save(self, entity: OrderCreatedModel) -> None:
        """Persist a created-order entity in the inventory database.

        Args:
            entity: The order payload to persist as a Peewee record.

        Returns:
            None. The order is stored in the database.
        """
        logger.info("Saving OrderCreatedModel: %s", entity)
        # Convert the Pydantic schema into a Peewee model row.
        OrderCreated.create(order_id=entity.order_id, items=entity.items)

    def get_by_id(self, entity_id: str) -> OrderCreatedModel | None:
        """Retrieve a stored order by its order identifier.

        Args:
            entity_id: The unique order identifier used as the lookup key.

        Returns:
            The matching order payload, or None if no record exists.
        """
        record = OrderCreated.get_or_none(OrderCreated.order_id == entity_id)
        if not record:
            return None
        return OrderCreatedModel(order_id=record.order_id, items=record.items)

    def delete(self, entity_id: str) -> None:
        """Delete a stored order using its order identifier.

        Args:
            entity_id: The unique order identifier to remove from storage.

        Returns:
            None. Matching rows are deleted from the database.
        """
        OrderCreated.delete().where(OrderCreated.order_id == entity_id).execute()

    def get_by_customer_id(self, customer_id: str) -> list[OrderCreatedModel]:
        """Fetch all orders associated with a customer identifier.

        Args:
            customer_id: The customer identifier used to filter the records.

        Returns:
            A list of order payloads matching the customer.
        """
        records = OrderCreated.select().where(OrderCreated.user_id == customer_id)
        return [OrderCreatedModel(order_id=r.order_id, items=r.items) for r in records]
