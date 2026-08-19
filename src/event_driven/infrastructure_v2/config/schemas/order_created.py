"""Auto-generated settings from YAML spec."""

from typing import Literal

from pydantic import AliasChoices, BaseModel, ConfigDict, Field

from .cart_item import CartItemModel


class OrderCreatedModel(BaseModel):
    """Settings for the orderCreated section."""

    model_config = ConfigDict(
        from_attributes=True,
        extra="ignore",
        populate_by_name=True,
    )

    type: Literal["OrderCreated"] = Field(default="OrderCreated", exclude=True)

    event_id: str = Field(
        default=888888,
        alias="eventId",
        validation_alias=AliasChoices("EVENT_ID", "eventId", "event_id"),
        description="Event id",
    )

    order_id: str = Field(
        default=9999999,
        alias="orderId",
        validation_alias=AliasChoices("ORDER_ID", "orderId", "order_id"),
        description="Order id",
    )

    user_id: str | None = Field(
        default=None,
        alias="userId",
        validation_alias=AliasChoices("USER_ID", "userId", "user_id"),
        description="User id",
    )

    items: list[CartItemModel] = Field(
        default=None, alias="items", validation_alias=AliasChoices("ITEMS", "items"), description="list of items"
    )

    timestamp: str = Field(
        default="timestamp.now",
        alias="timestamp",
        validation_alias=AliasChoices("TIMESTAMP", "timestamp"),
        description="Order timestamp",
    )
