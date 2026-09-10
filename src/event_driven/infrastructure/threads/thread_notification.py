"""Notification worker thread implementation."""

import logging

from event_driven.domain.schemas import NotificationModel
from event_driven.infrastructure.config.schemas import ThreadConfigModel

from ...domain.use_case import NotificationUseCase
from .thread_base import BaseWorkerThread

logger = logging.getLogger(__name__)


class NotificationThread(BaseWorkerThread[NotificationModel, NotificationModel]):
    """Worker that sends user-facing notifications after processing is complete."""

    def __init__(
        self,
        config: ThreadConfigModel,
    ) -> None:
        """Initialize the notification worker and bind it to the incoming topic."""
        super().__init__(config=config, payload_model=NotificationModel)

        self.use_case = NotificationUseCase()

    def process_payload(self, payload: NotificationModel) -> NotificationModel | None:
        """Process a notification payload and emit the user alert."""
        logger.info("Sending notification to user...")
        return self.use_case.execute(payload)
