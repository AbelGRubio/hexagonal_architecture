"""Auto-generated settings from YAML spec."""

from datetime import datetime
from typing import Literal

from pydantic import AliasChoices, BaseModel, ConfigDict, Field

from event_driven.domain.schemas import CartItemModel


class OrderCreatedModel(BaseModel):
    """Settings for the order Created section."""

    model_config = ConfigDict(
        from_attributes=True,
        extra="ignore",
        populate_by_name=True,
    )

    type: Literal["OrderCreated"] = Field(default="OrderCreated", exclude=True)

    event_id: str = Field(
        default="888xxx",
        alias="eventId",
        validation_alias=AliasChoices("EVENT_ID", "eventId", "event_id"),
        description="Event id",
    )

    items: list[CartItemModel] = Field(
        default=[], alias="items", validation_alias=AliasChoices("ITEMS", "items"), description="list of items"
    )

    order_id: str = Field(
        default="9999xxx",
        alias="orderId",
        validation_alias=AliasChoices("ORDER_ID", "orderId", "order_id"),
        description="Order id",
    )

    timestamp: datetime | None = Field(
        default=datetime.now(),
        alias="timestamp",
        validation_alias=AliasChoices("TIMESTAMP", "timestamp"),
        description="Order timestamp",
    )

    user_id: str | None = Field(
        default=None,
        alias="userId",
        validation_alias=AliasChoices("USER_ID", "userId", "user_id"),
        description="User id",
    )
