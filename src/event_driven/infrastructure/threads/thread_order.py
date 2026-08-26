"""Order worker thread implementation."""
from typing import Optional

from pydantic import BaseModel

from event_driven.infrastructure.config.schemas import ThreadConfigModel
from event_driven.logger import get_logger

from .thread_base import BaseWorkerThread

logger = get_logger(__name__)


class OrderThread(BaseWorkerThread[BaseModel, BaseModel]):
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

    def process_payload(self, payload: BaseModel) -> Optional[BaseModel]:
        """Process a validated order payload."""
        logger.info(f"[{self.name}] Processing order: {payload}")
        return None
