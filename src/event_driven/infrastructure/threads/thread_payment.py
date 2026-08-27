"""Payment worker thread implementation."""
from typing import Optional

from pydantic import BaseModel


from event_driven.infrastructure.config.schemas import ThreadConfigModel
from event_driven.logger import get_logger
from event_driven.domain.schemas import PaymentModel, NotificationModel

from .thread_base import BaseWorkerThread
from event_driven.domain.use_case.case_payment import PaymentUseCase

logger = get_logger(__name__)


class PaymentThread(BaseWorkerThread[PaymentModel, NotificationModel]):
    """Worker responsible for processing payment-related events."""

    def __init__(
        self,
        config: ThreadConfigModel,
    ) -> None:
        """Initialize the payment worker and link it to its message destinations."""
        super().__init__(
            payload_model=PaymentModel,
            config=config
        )

        self.use_case = PaymentUseCase()

    def process_payload(self, payload: PaymentModel) -> Optional[NotificationModel]:
        """Process a validated payment payload."""
        logger.info(f"Processing payment...")
        return self.use_case.execute(payload)
