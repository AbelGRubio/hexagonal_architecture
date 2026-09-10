"""Auto-generated settings from YAML spec."""

from datetime import datetime
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

    channel: str = Field(
        default="EMAIL",
        alias="channel",
        validation_alias=AliasChoices("CHANNEL", "channel"),
        description="Channel used to deliver the notification",
    )

    event_id: str = Field(
        default="666xxx",
        alias="eventId",
        validation_alias=AliasChoices("EVENT_ID", "eventId", "event_id"),
        description="Event id",
    )

    message: str = Field(
        default="NoContent",
        alias="message",
        validation_alias=AliasChoices("MESSAGE", "message"),
        description="Body content of the notification",
    )

    notification_id: str = Field(
        default="notif_111xxx",
        alias="notificationId",
        validation_alias=AliasChoices("NOTIFICATION_ID", "notificationId", "notification_id"),
        description="Notification identification",
    )

    order_id: str = Field(
        default="9999xxx",
        alias="orderId",
        validation_alias=AliasChoices("ORDER_ID", "orderId", "order_id"),
        description="Associated Order id",
    )

    recipient: str = Field(
        ...,
        alias="recipient",
        validation_alias=AliasChoices("RECIPIENT", "recipient"),
        description="Recipient of the notification",
    )

    status: str = Field(
        default="PENDING",
        alias="status",
        validation_alias=AliasChoices("STATUS", "status"),
        description="Delivery status of the notification",
    )

    subject: str = Field(
        default="Order Update",
        alias="subject",
        validation_alias=AliasChoices("SUBJECT", "subject"),
        description="Subject of the notification",
    )

    timestamp: datetime | None = Field(
        default=datetime.now(),
        alias="timestamp",
        validation_alias=AliasChoices("TIMESTAMP", "timestamp"),
        description="Notification timestamp",
    )

    user_id: str | None = Field(
        default=None,
        alias="userId",
        validation_alias=AliasChoices("USER_ID", "userId", "user_id"),
        description="User id recipient",
    )
