"""Notification worker thread implementation."""

import logging

from pydantic import BaseModel

from event_driven.domain.schemas import NotificationModel
from event_driven.infrastructure.config.schemas import ThreadConfigModel

from .thread_base import BaseWorkerThread

logger = logging.getLogger(__name__)


class NotificationThread(BaseWorkerThread[NotificationModel, BaseModel]):
    """Worker that sends user-facing notifications after processing is complete."""

    def __init__(
        self,
        config: ThreadConfigModel,
    ) -> None:
        """Initialize the notification worker and bind it to the incoming topic."""
        super().__init__(
            config=config,
            payload_model=NotificationModel
        )

    def process_payload(self, payload: NotificationModel) -> BaseModel | None:
        """Process a notification payload and emit the user alert."""
        logger.info(f"[{self.name}] Sending notification to user...")
        return None
