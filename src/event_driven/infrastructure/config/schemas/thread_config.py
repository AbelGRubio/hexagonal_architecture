"""Auto-generated settings from YAML spec."""

from typing import Literal

from pydantic import AliasChoices, BaseModel, ConfigDict, Field

from event_driven.infrastructure.config.enumerations import ThreadsEnum
from event_driven.infrastructure.config.schemas import BrokerConfigModel


class ThreadConfigModel(BaseModel):
    """Settings for the Thread Config section."""

    model_config = ConfigDict(
        from_attributes=True,
        extra="ignore",
        populate_by_name=True,
    )

    type: Literal["ThreadConfig"] = Field(default="ThreadConfig", exclude=True)

    consumer: BrokerConfigModel | None = Field(
        default=None,
        alias="consumer",
        validation_alias=AliasChoices("CONSUMER", "consumer"),
        description="Configuration for consuming messages. Set to None for producer-only threads.",
    )

    error: BrokerConfigModel | None = Field(
        default=None,
        alias="error",
        validation_alias=AliasChoices("ERROR", "error"),
        description="Configuration for Dead Letter Queue (DLQ) or error publishing.",
    )

    name: ThreadsEnum = Field(
        default=ThreadsEnum.WITHOUT_ASSIGNATION,
        alias="name",
        validation_alias=AliasChoices("NAME", "name"),
        description="Thread name.",
    )

    producer: BrokerConfigModel | None = Field(
        default=None,
        alias="producer",
        validation_alias=AliasChoices("PRODUCER", "producer"),
        description="Configuration for publishing successful output messages.",
    )
