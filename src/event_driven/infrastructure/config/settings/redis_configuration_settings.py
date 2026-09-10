"""Auto-generated settings from YAML spec."""

from pydantic import AliasChoices, Field
from pydantic_settings import SettingsConfigDict

from .base_settings import BaseTraceableSettings


class RedisConfigurationSettings(BaseTraceableSettings):
    """Settings for the Redis Configuration section."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_ignore_empty=True,
        env_prefix="REDIS__",
        env_nested_delimiter="__",
        case_sensitive=False,
        env_prefix_target="all",
        from_attributes=True,
        extra="ignore",
        populate_by_name=True,
    )

    db: int = Field(
        default=0, alias="db", validation_alias=AliasChoices("DB", "db"), description="Redis database index"
    )

    decode_responses: bool = Field(
        default=False,
        alias="decodeResponses",
        validation_alias=AliasChoices("DECODE_RESPONSES", "decodeResponses", "decode_responses"),
        description="Decode responses as strings.",
    )

    host: str = Field(
        default="localhost", alias="host", validation_alias=AliasChoices("HOST", "host"), description="Redis host"
    )

    port: int = Field(
        default=6379, alias="port", validation_alias=AliasChoices("PORT", "port"), description="Redis port"
    )
