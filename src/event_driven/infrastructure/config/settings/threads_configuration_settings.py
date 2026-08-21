"""Auto-generated settings from YAML spec."""

from pydantic import AliasChoices, Field
from pydantic_settings import SettingsConfigDict

from event_driven.infrastructure.config.schemas import ThreadConfigModel

from .base_settings import BaseTraceableSettings


class ThreadsConfigurationSettings(BaseTraceableSettings):
    """Settings for the Threads Configuration section."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_ignore_empty=True,
        env_prefix="_",
        env_nested_delimiter="__",
        case_sensitive=False,
        env_prefix_target="all",
        from_attributes=True,
        extra="ignore",
        populate_by_name=True,
    )

    configuration: list[ThreadConfigModel] | None = Field(
        default=None,
        alias="configuration",
        validation_alias=AliasChoices("CONFIGURATION", "configuration"),
        description="threads configurations",
    )
