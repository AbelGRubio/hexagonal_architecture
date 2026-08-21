"""Auto-generated settings from YAML spec."""

from typing import Literal

from pydantic import AliasChoices, BaseModel, ConfigDict, Field


class NotificationModel(BaseModel):
    """Settings for the Notification section."""

    model_config = ConfigDict(
        from_attributes=True,
        extra="ignore",
        populate_by_name=True,
    )

    type: Literal["Notification"] = Field(default="Notification", exclude=True)

    content: str | None = Field(
        default=None,
        alias="content",
        validation_alias=AliasChoices("CONTENT", "content"),
        description="message content",
    )

    notification_id: str = Field(
        default="xxxx7",
        alias="notificationId",
        validation_alias=AliasChoices("NOTIFICATION_ID", "notificationId", "notification_id"),
        description="notification id",
    )

    user_id: str | None = Field(
        default=None,
        alias="userId",
        validation_alias=AliasChoices("USER_ID", "userId", "user_id"),
        description="User name",
    )
