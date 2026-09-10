from logging import getLogger

from event_driven.domain.ports import BasePort
from event_driven.domain.schemas import OrderCreatedModel
from event_driven.infrastructure.persistence.models import OrderCreated

logger = getLogger(__name__)


class AdapterCheckInventory(BasePort):
    """Concrete Peewee ORM adapter implementing BasePort."""

    def save(self, entity: OrderCreatedModel) -> None:
        logger.info(f"Saving OrderCreatedModel: {entity}")
        # Convert Pydantic schema to Peewee ORM model
        OrderCreated.create(order_id=entity.order_id, items=entity.items)

    def get_by_id(self, entity_id: str) -> OrderCreatedModel | None:
        record = OrderCreated.get_or_none(OrderCreated.order_id == entity_id)
        if not record:
            return None
        return OrderCreatedModel(order_id=record.order_id, items=record.items)

    def delete(self, entity_id: str) -> None:
        OrderCreated.delete().where(OrderCreated.order_id == entity_id).execute()

    def get_by_customer_id(self, customer_id: str) -> list[OrderCreatedModel]:
        records = OrderCreated.select().where(OrderCreated.user_id == customer_id)
        return [OrderCreatedModel(order_id=r.order_id, items=r.items) for r in records]
