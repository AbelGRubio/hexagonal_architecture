"""Payment worker thread implementation."""

from pydantic import BaseModel


from event_driven.infrastructure.config.schemas import ThreadConfigModel
from event_driven.logger import get_logger

from .thread_base import BaseWorkerThread

logger = get_logger(__name__)


class PaymentThread(BaseWorkerThread[BaseModel, BaseModel]):
    """Worker responsible for processing payment-related events."""

    def __init__(
        self,
        config: ThreadConfigModel,
    ) -> None:
        """Initialize the payment worker and link it to its message destinations."""
        super().__init__(
            payload_model=BaseModel,
            config=config
        )

    def process_payload(self, payload: BaseModel) -> BaseModel | None:
        """Process a validated payment payload."""
        logger.info(f"[{self.name}] Processing payment...")
        return None
