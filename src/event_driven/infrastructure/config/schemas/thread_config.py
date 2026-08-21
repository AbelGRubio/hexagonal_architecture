"""Auto-generated settings from YAML spec."""

from typing import Literal

from pydantic import AliasChoices, BaseModel, ConfigDict, Field

from event_driven.infrastructure.config.schemas import QueueConfigModel


class ThreadConfigModel(BaseModel):
    """Settings for the Thread Config section."""

    model_config = ConfigDict(
        from_attributes=True,
        extra="ignore",
        populate_by_name=True,
    )

    type: Literal["ThreadConfig"] = Field(default="ThreadConfig", exclude=True)

    input: QueueConfigModel | None = Field(
        default=None, alias="input", validation_alias=AliasChoices("INPUT", "input"), description="Input configuration."
    )

    name: str | None = Field(
        default=None, alias="name", validation_alias=AliasChoices("NAME", "name"), description="Thread name."
    )

    output: QueueConfigModel | None = Field(
        default=None,
        alias="output",
        validation_alias=AliasChoices("OUTPUT", "output"),
        description="Output configuration.",
    )
