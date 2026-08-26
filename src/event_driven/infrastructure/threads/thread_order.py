"""Order worker thread implementation."""
from typing import Optional

from pydantic import BaseModel

from event_driven.infrastructure.config.schemas import ThreadConfigModel
from event_driven.logger import get_logger
from event_driven.domain.schemas.order_created import OrderCreatedModel
from .thread_base import BaseWorkerThread
from ..persistence.adapter import AdapterOrderCreated
from ...domain.use_case.case_process_order import ProcessOrderUseCase

logger = get_logger(__name__)


class OrderThread(BaseWorkerThread[OrderCreatedModel, BaseModel]):
    """Worker that processes order creation or order-related events."""

    def __init__(
        self,
        config: ThreadConfigModel,
    ) -> None:
        """Initialize the order worker with its input and output message topics."""
        super().__init__(
            config=config,
            payload_model=BaseModel,
        )

        db_adapter = AdapterOrderCreated()

        self.use_case = ProcessOrderUseCase(adapter=db_adapter)

    def process_payload(self, payload: OrderCreatedModel) -> Optional[BaseModel]:
        """Process a validated order payload."""
        logger.info(f"[{self.name}] Processing order: {payload}")
        self.use_case.execute(payload)
        return None
