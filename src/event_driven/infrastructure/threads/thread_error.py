"""Error processor worker thread implementation.

This worker consumes error/DLQ messages and performs handling such as
logging, alerting or attempted compensation/replay. Keep the implementation
simple: parse the standard ErrorEnvelope defined in thread_base and log the
content. Extend later to integrate alerting or automated retries.
"""

import logging
from typing import Optional

from event_driven.infrastructure.config.schemas import ThreadConfigModel
from event_driven.infrastructure.threads.thread_base import BaseWorkerThread, ErrorEnvelope

logger = logging.getLogger(__name__)


class ErrorThread(BaseWorkerThread[ErrorEnvelope, None]):
    """Worker that processes error/envelope messages from DLQ."""

    def __init__(self, config: ThreadConfigModel) -> None:
        super().__init__(config=config, payload_model=ErrorEnvelope)

    def process_payload(self, payload: ErrorEnvelope) -> Optional[None]:
        """Handle the error envelope.

        Current behavior: log the failure details. This is intentionally simple
        so teams can plug in alerting, metrics, or replay logic later.
        """
        try:
            logger.error(
                f"[ErrorThread] Received error envelope: type={payload.error_type} "
                f"message={payload.error_message} failed_payload={payload.failed_payload}"
            )
            # Placeholder: extend with alerting, metrics, or automated retry logic.
        except Exception as exc:  # pragma: no cover - safety logging
            logger.exception(f"[ErrorThread] Exception while handling error envelope: {exc}")

        # No output message to produce by default
        return None
