"""Auto-generated settings from YAML spec."""

from datetime import datetime
from typing import Literal

from pydantic import AliasChoices, BaseModel, ConfigDict, Field

from event_driven.domain.enumerations import PaymentStatusEnum
from event_driven.domain.schemas import CartItemModel


class CartPaymentModel(BaseModel):
    """Settings for the CartPayment section."""

    model_config = ConfigDict(
        from_attributes=True,
        extra="ignore",
        populate_by_name=True,
    )

    type: Literal["CartPayment"] = Field(default="CartPayment", exclude=True)

    amount: float = Field(
        default=0.0,
        alias="amount",
        validation_alias=AliasChoices("AMOUNT", "amount"),
        description="Total payment amount",
    )

    card_brand: str | None = Field(
        default=None,
        alias="cardBrand",
        validation_alias=AliasChoices("CARD_BRAND", "cardBrand", "card_brand"),
        description="Card brand",
    )

    card_last4: str | None = Field(
        default=None,
        alias="cardLast4",
        validation_alias=AliasChoices("CARD_LAST4", "cardLast4", "card_last4"),
        description="Last 4 digits of card",
    )

    cart_id: str = Field(
        default="cart_000",
        alias="cartId",
        validation_alias=AliasChoices("CART_ID", "cartId", "cart_id"),
        description="Cart identification",
    )

    currency: str = Field(
        default="EUR",
        alias="currency",
        validation_alias=AliasChoices("CURRENCY", "currency"),
        description="Currency code (e.g. EUR, USD)",
    )

    items: list[CartItemModel] = Field(
        default=[], alias="items", validation_alias=AliasChoices("ITEMS", "items"), description="List of cart items"
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

    status: PaymentStatusEnum = Field(
        default=PaymentStatusEnum.PENDING,
        alias="status",
        validation_alias=AliasChoices("STATUS", "status"),
        description="Card payment status",
    )

    timestamp: datetime | None = Field(
        default=datetime.now(),
        alias="timestamp",
        validation_alias=AliasChoices("TIMESTAMP", "timestamp"),
        description="Payment processing timestamp",
    )

    transaction_id: str | None = Field(
        default=None,
        alias="transactionId",
        validation_alias=AliasChoices("TRANSACTION_ID", "transactionId", "transaction_id"),
        description="Processor transaction id",
    )

    user_id: str | None = Field(
        default=None,
        alias="userId",
        validation_alias=AliasChoices("USER_ID", "userId", "user_id"),
        description="User id",
    )
