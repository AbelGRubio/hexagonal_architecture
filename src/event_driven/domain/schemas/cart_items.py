"""Auto-generated settings from YAML spec."""

from typing import Literal

from pydantic import AliasChoices, BaseModel, ConfigDict, Field

from event_driven.domain.schemas import CartItemModel


class CartItemsModel(BaseModel):
    """Settings for the CartItems section."""

    model_config = ConfigDict(
        from_attributes=True,
        extra="ignore",
        populate_by_name=True,
    )

    type: Literal["CartItems"] = Field(default="CartItems", exclude=True)

    id: str = Field(
        default="NoIdentified", alias="id", validation_alias=AliasChoices("ID", "id"), description="Cart identification"
    )

    items: list[CartItemModel] = Field(
        default=[], alias="items", validation_alias=AliasChoices("ITEMS", "items"), description="List of item"
    )
