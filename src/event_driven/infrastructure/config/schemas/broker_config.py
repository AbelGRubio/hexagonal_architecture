"""Auto-generated settings from YAML spec."""

from typing import Literal

from pydantic import AliasChoices, BaseModel, ConfigDict, Field

from event_driven.infrastructure.config.enumerations import BrokersEnum


class BrokerConfigModel(BaseModel):
    """Settings for the Broker Config section."""

    model_config = ConfigDict(
        from_attributes=True,
        extra="ignore",
        populate_by_name=True,
    )

    type: Literal["BrokerConfig"] = Field(default="BrokerConfig", exclude=True)

    broker_kwargs: dict = Field(
        default={},
        alias="brokerKwargs",
        validation_alias=AliasChoices("BROKER_KWARGS", "brokerKwargs", "broker_kwargs"),
        description="Connection parameters for initializing the IMessageBroker adapter.",
    )

    broker_type: BrokersEnum = Field(
        default=BrokersEnum.KAFKA,
        alias="brokerType",
        validation_alias=AliasChoices("BROKER_TYPE", "brokerType", "broker_type"),
        description="Broker type 'Local', 'Kafka' or 'RabbitMQ'.",
    )

    exchange: str | None = Field(
        default=None,
        alias="exchange",
        validation_alias=AliasChoices("EXCHANGE", "exchange"),
        description="exchange name",
    )

    topic_or_queue: str = Field(
        ...,
        alias="topicOrQueue",
        validation_alias=AliasChoices("TOPIC_OR_QUEUE", "topicOrQueue", "topic_or_queue"),
        description="topic or queue name",
    )
