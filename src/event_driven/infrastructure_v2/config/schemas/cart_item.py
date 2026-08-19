"""Auto-generated settings from YAML spec."""

from typing import Literal

from pydantic import AliasChoices, BaseModel, ConfigDict, Field


class CartItemModel(BaseModel):
    """Settings for the CartItem section."""

    model_config = ConfigDict(
        from_attributes=True,
        extra="ignore",
        populate_by_name=True,
    )

    type: Literal["CartItem"] = Field(default="CartItem", exclude=True)

    product_id: str = Field(
        default="xxxxxx",
        alias="productId",
        validation_alias=AliasChoices("PRODUCT_ID", "productId", "product_id"),
        description="Product id",
    )

    name: str | None = Field(
        default=None, alias="name", validation_alias=AliasChoices("NAME", "name"), description="Product name"
    )

    quantity: int = Field(
        default=0, alias="quantity", validation_alias=AliasChoices("QUANTITY", "quantity"), description="Quantity"
    )

    unit_price: float = Field(
        default=0,
        alias="unitPrice",
        validation_alias=AliasChoices("UNIT_PRICE", "unitPrice", "unit_price"),
        description="Item unit price",
    )
