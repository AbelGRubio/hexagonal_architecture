"""Base worker thread implementation for event-driven processing.

This module defines the reusable worker lifecycle used to consume messages,
validate payloads, execute business logic, and publish results or DLQ events.
"""

import abc
import json
import logging
import threading
import traceback
from typing import Any, Callable, Generator, Generic, TypeVar

from pydantic import BaseModel, ValidationError

from event_driven.infrastructure.messaging.brokers.interface_message import IMessageBroker

logger = logging.getLogger(__name__)

PayloadT = TypeVar("PayloadT", bound=BaseModel)
OutputT = TypeVar("OutputT", bound=BaseModel)


class ErrorEnvelope(BaseModel):
    """Standard payload used to publish messages into the dead-letter queue."""

    failed_payload: Any
    error_type: str
    error_message: str
    traceback: str | None = None


class BaseWorkerThread(threading.Thread, abc.ABC, Generic[PayloadT, OutputT]):
    """Abstract base worker executed in its own dedicated thread.

    The thread consumes raw messages from a broker, validates them against a
    Pydantic model, invokes business logic, and publishes the output or pushes
    any failure into a DLQ.
    """

    def __init__(
        self,
        payload_model: type[PayloadT],
        broker: IMessageBroker,
        consume_destination: str,
        publish_destination: str | None = None,
        dlq_destination: str | None = None,
        name: str | None = None,
        daemon: bool = True,
    ) -> None:
        """Initialize the worker thread and store the broker configuration."""
        name_ = name or type(self).__name__
        super().__init__(name=name, daemon=daemon)
        self.payload_model: type[PayloadT] = payload_model
        self.broker: IMessageBroker = broker
        self.consume_destination: str = consume_destination
        self.publish_destination: str | None = publish_destination
        self.dlq_destination: str | None = dlq_destination or publish_destination or f"{name_}-errors"
        self._is_running: bool = True

    @abc.abstractmethod
    def process_payload(self, payload: PayloadT) -> OutputT | None:
        """Execute the worker's business logic for a validated message.

        Args:
            payload: Validated Pydantic model instance.

        Returns:
            An output model to be published, or `None` when no output is required.
        """
        return NotImplemented

    def handle_validation_error(self, raw_message: Any, error: Exception) -> None:
        """Handle schema or JSON validation failures by publishing them to the DLQ."""
        logger.error(f"[{self.name}] Validation error: {error}")
        self._publish_to_dlq(payload=raw_message, error=error, reason="Validation Error")

    def handle_processing_error(self, payload: PayloadT, error: Exception) -> None:
        """Handle uncaught processing exceptions and route them to the DLQ."""
        logger.error(f"[{self.name}] Processing error with payload {payload}: {error}")

        payload_data = payload.model_dump() if isinstance(payload, BaseModel) else payload

        self._publish_to_dlq(payload=payload_data, error=error, reason="Processing Error")

    def stop(self) -> None:
        """Signal the worker loop to exit gracefully."""
        logger.info(f"Stop signal received '{self.name}'")
        self._is_running = False

    def read_raw_message(self) -> Generator[Any, None, None]:
        """Fetch the next raw message from the configured broker."""
        return self.broker.consume(self.consume_destination)

    def send_output_message(self, result: OutputT) -> None:
        """Publish the successful processing output to the configured destination."""
        if self.publish_destination and self.broker:
            try:
                payload_str = str(result.model_dump_json())
                self.broker.publish(self.publish_destination, payload_str)
            except Exception as exc:
                logger.error(f"Error publishing message from '{self.name}': {exc}")
        else:
            logger.warning(f"[{self.name}] Output generated but no publish_destination or broker configured.")

    def run(self) -> None:
        """Run the worker loop in the background thread."""
        logger.info(f"Worker thread '{self.name}' started.")

        for raw_message in self.read_raw_message():
            if not self._is_running:
                logger.info(f"Signal received from thread '{self.name}' stopped. State {self._is_running}")
                break

            if raw_message is None:
                logger.info(f"Waiting for the item to process. {self._is_running}")
                continue

            parsed_payload = self._parse_message(raw_message)
            if parsed_payload is None:
                continue

            try:
                result = self.process_payload(parsed_payload)
            except Exception as proc_err:
                logger.error(f"Processing error in thread '{self.name}': {proc_err}")
                self.handle_processing_error(parsed_payload, proc_err)
                continue

            if result is not None:
                self.send_output_message(result)

        logger.info(f"Worker thread '{self.name}' stopped.")

    def _parse_message(self, raw_message: Any) -> PayloadT | None:
        """Deserialize a raw message into the expected Pydantic model.

        Args:
            raw_message: Raw broker payload, such as JSON string, bytes, or dict.

        Returns:
            A validated Pydantic payload instance, or `None` if validation fails.
        """
        try:
            if isinstance(raw_message, (str, bytes)):
                data_dict: dict[str, Any] = json.loads(raw_message)
            elif isinstance(raw_message, dict):
                data_dict = raw_message
            else:
                raise ValueError(f"Unsupported payload type: {type(raw_message)}")

            return self.payload_model.model_validate(data_dict)

        except (json.JSONDecodeError, ValidationError, ValueError) as err:
            logger.warning(f"Schema validation failed for incoming message in '{self.name}' thread.")

            if not isinstance(err, ValidationError):
                err = ValidationError.from_exception_data(
                    title=self.payload_model.__name__,
                    line_errors=[],
                )
            self.handle_validation_error(raw_message, err)
            return None

    def _publish_to_dlq(self, payload: Any, error: Exception, reason: str) -> None:
        """Send a failed message and its metadata to the configured DLQ destination."""
        if not self.dlq_destination:
            logger.warning(f"[{self.name}] Failed to dispatch error: no dlq_destination configured.")
            return

        try:
            error_event = ErrorEnvelope(
                failed_payload=payload,
                error_type=f"{reason}: {type(error).__name__}",
                error_message=str(error),
                traceback=traceback.format_exc(),
            )
            self.broker.publish(self.dlq_destination, error_event.model_dump_json())
            logger.info(f"[{self.name}] Message successfully routed to DLQ '{self.dlq_destination}'.")
        except Exception as dlq_err:
            logger.critical(f"[{self.name}] Critical failure sending message to DLQ: {dlq_err}")
