"""Auto-generated settings from YAML spec."""

from datetime import datetime
from typing import Literal

from pydantic import AliasChoices, BaseModel, ConfigDict, Field


class PaymentModel(BaseModel):
    """Settings for the Payment section."""

    model_config = ConfigDict(
        from_attributes=True,
        extra="ignore",
        populate_by_name=True,
    )

    type: Literal["Payment"] = Field(default="Payment", exclude=True)

    amount: float = Field(
        default=0.0,
        alias="amount",
        validation_alias=AliasChoices("AMOUNT", "amount"),
        description="Total payment amount",
    )

    currency: str = Field(
        default="EUR",
        alias="currency",
        validation_alias=AliasChoices("CURRENCY", "currency"),
        description="Currency code (e.g. EUR, USD)",
    )

    event_id: str = Field(
        default="777xxx",
        alias="eventId",
        validation_alias=AliasChoices("EVENT_ID", "eventId", "event_id"),
        description="Event id",
    )

    order_id: str = Field(
        default="9999xxx",
        alias="orderId",
        validation_alias=AliasChoices("ORDER_ID", "orderId", "order_id"),
        description="Order id associated with the payment",
    )

    payment_id: str = Field(
        default="pay_999xxx",
        alias="paymentId",
        validation_alias=AliasChoices("PAYMENT_ID", "paymentId", "payment_id"),
        description="Payment identification",
    )

    payment_method: str = Field(
        default="CREDIT_CARD",
        alias="paymentMethod",
        validation_alias=AliasChoices("PAYMENT_METHOD", "paymentMethod", "payment_method"),
        description="Payment method used",
    )

    status: str = Field(
        default="PENDING",
        alias="status",
        validation_alias=AliasChoices("STATUS", "status"),
        description="Payment processing status",
    )

    timestamp: datetime | None = Field(
        default=datetime.now(),
        alias="timestamp",
        validation_alias=AliasChoices("TIMESTAMP", "timestamp"),
        description="Payment processing timestamp",
    )

    user_id: str | None = Field(
        default=None,
        alias="userId",
        validation_alias=AliasChoices("USER_ID", "userId", "user_id"),
        description="User id",
    )
