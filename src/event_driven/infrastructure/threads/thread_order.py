"""Order worker thread implementation."""
from typing import Optional

from event_driven.domain.schemas import OrderCreatedModel, PaymentModel
from event_driven.domain.use_case.case_process_order import ProcessOrderUseCase
from event_driven.infrastructure.config.schemas import ThreadConfigModel
from event_driven.infrastructure.persistence.adapter import AdapterOrderCreated
from event_driven.infrastructure.threads.thread_base import BaseWorkerThread
from event_driven.logger import get_logger

logger = get_logger(__name__)


class OrderThread(BaseWorkerThread[OrderCreatedModel, PaymentModel]):
    """Worker that processes order creation or order-related events."""

    def __init__(
        self,
        config: ThreadConfigModel,
    ) -> None:
        """Initialize the order worker with its input and output message topics."""
        super().__init__(
            config=config,
            payload_model=OrderCreatedModel,
        )

        db_adapter = AdapterOrderCreated()

        self.use_case = ProcessOrderUseCase(adapter=db_adapter)

    def process_payload(self, payload: OrderCreatedModel) -> Optional[PaymentModel]:
        """Process a validated order payload."""
        logger.info(f"Processing order: {payload}")
        return self.use_case.execute(payload)
