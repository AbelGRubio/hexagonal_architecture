"""Payment worker thread implementation."""

from event_driven.domain.schemas import NotificationModel, PaymentModel
from event_driven.domain.use_case.case_payment import PaymentUseCase
from event_driven.infrastructure.config.schemas import ThreadConfigModel
from event_driven.logger import get_logger

from .thread_base import BaseWorkerThread

logger = get_logger(__name__)


class PaymentThread(BaseWorkerThread[PaymentModel, NotificationModel]):
    """Worker responsible for processing payment-related events."""

    def __init__(
        self,
        config: ThreadConfigModel,
    ) -> None:
        """Initialize the payment worker and link it to its message destinations."""
        super().__init__(payload_model=PaymentModel, config=config)

        self.use_case = PaymentUseCase()

    def process_payload(self, payload: PaymentModel) -> NotificationModel | None:
        """Process a validated payment payload."""
        logger.info("Processing payment...")
        return self.use_case.execute(payload)
