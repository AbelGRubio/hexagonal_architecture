"""Auto-generated settings from YAML spec."""

from pydantic import AliasChoices, Field, SecretStr
from pydantic_settings import SettingsConfigDict

from .base_settings import BaseTraceableSettings


class AwsConfigurationSettings(BaseTraceableSettings):
    """Settings for the AWS Configuration section."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_ignore_empty=True,
        env_prefix="AWS__",
        env_nested_delimiter="__",
        case_sensitive=False,
        env_prefix_target="all",
        from_attributes=True,
        extra="ignore",
        populate_by_name=True,
    )

    access_key_id: SecretStr = Field(
        default=SecretStr(""),
        alias="accessKeyId",
        validation_alias=AliasChoices("ACCESS_KEY_ID", "accessKeyId", "access_key_id"),
        description="Access key id",
    )

    default_region: str | None = Field(
        default=None,
        alias="defaultRegion",
        validation_alias=AliasChoices("DEFAULT_REGION", "defaultRegion", "default_region"),
        description="default region",
    )

    s3_endpoint_url: str | None = Field(
        default=None,
        alias="s3EndpointUrl",
        validation_alias=AliasChoices("S3_ENDPOINT_URL", "s3EndpointUrl", "s3_endpoint_url"),
        description="s3 endpoint url",
    )
