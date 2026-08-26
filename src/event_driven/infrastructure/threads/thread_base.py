"""Base worker thread implementation for event-driven processing.

This module defines the reusable worker lifecycle used to consume messages,
validate payloads, execute business logic, and publish results or DLQ events
using structured thread and broker configurations.
"""

import abc
import json
import logging
import threading
import traceback
from typing import Any, Generator, Generic, TypeVar, Optional

from pydantic import BaseModel, ValidationError

from event_driven.infrastructure.config.schemas import BrokerConfigModel, ThreadConfigModel
from event_driven.infrastructure.messaging.brokers import IMessageBroker
from event_driven.infrastructure.messaging import MessageBrokerFactory


logger = logging.getLogger(__name__)

PayloadT = TypeVar("PayloadT", bound=BaseModel | None)
OutputT = TypeVar("OutputT", bound=BaseModel | None)


class ErrorEnvelope(BaseModel):
    """Standard payload used to publish messages into the dead-letter queue."""

    failed_payload: Any
    error_type: str
    error_message: str
    traceback: str | None = None


class BaseWorkerThread(threading.Thread, abc.ABC, Generic[PayloadT, OutputT]):
    """Abstract base worker executed in its own dedicated thread.

    Consumes raw messages from a consumer broker, validates them against a
    Pydantic model, invokes business logic, and publishes output or failure
    events to their designated target brokers.
    """

    def __init__(
        self,
        config: ThreadConfigModel,
        payload_model: type[PayloadT] | None = None,
        daemon: bool = True,
    ) -> None:
        """Initialize the worker thread configuration and broker factory.

        Args:
            config: Thread configuration model containing consumer, producer, and error settings.
            payload_model: Optional Pydantic payload model class for validation (None for producer-only threads).
            daemon: Whether the thread runs as a daemon.
        """
        thread_name = config.name or type(self).__name__
        super().__init__(name=thread_name, daemon=daemon)

        self.config: ThreadConfigModel = config
        self.broker_factory: MessageBrokerFactory = MessageBrokerFactory()
        self.payload_model: type[PayloadT] | None = payload_model
        self._is_running: bool = True

        # Thread-local broker client instances initialized inside run()
        self.consumer_broker: IMessageBroker | None = None
        self.producer_broker: IMessageBroker | None = None
        self.error_broker: IMessageBroker | None = None

    def _init_brokers(self) -> None:
        """Instantiate thread-local broker instances using the provided factory."""
        if self.config.consumer:
            aux_ = self.config.consumer
            kwargs_ = aux_.broker_kwargs or {}
            self.consumer_broker = self.broker_factory.create_broker(aux_.broker_type, **kwargs_)

        if self.config.producer:
            aux_ = self.config.producer
            kwargs_ = aux_.broker_kwargs or {}
            self.producer_broker = self.broker_factory.create_broker(aux_.broker_type, **kwargs_)

        if self.config.error:
            aux_ = self.config.error
            kwargs_ = aux_.broker_kwargs or {}
            self.error_broker = self.broker_factory.create_broker(aux_.broker_type, **kwargs_)

    @abc.abstractmethod
    def process_payload(self, payload: PayloadT) -> Optional[OutputT]:
        """Execute worker business logic for a validated message.

        Args:
            payload: Validated payload model instance.

        Returns:
            An output model instance or None.
        """
        return NotImplemented

    def handle_validation_error(self, raw_message: Any, error: Exception) -> None:
        """Route schema or deserialization failures to the DLQ."""
        logger.error(f"[{self.name}] Validation error: {error}")
        self._publish_to_dlq(payload=raw_message, error=error, reason="Validation Error")

    def handle_processing_error(self, payload: PayloadT, error: Exception) -> None:
        """Route uncaught processing exceptions to the DLQ."""
        logger.error(f"[{self.name}] Processing error with payload {payload}: {error}")
        payload_data = payload.model_dump() if isinstance(payload, BaseModel) else payload
        self._publish_to_dlq(payload=payload_data, error=error, reason="Processing Error")

    def stop(self) -> None:
        """Signal the worker loop to exit gracefully."""
        logger.info(f"Stop signal received for worker '{self.name}'.")
        self._is_running = False

    def read_raw_message(self) -> Generator[Any, None, None]:
        """Fetch raw messages from the consumer broker."""
        if not self.consumer_broker or not self.config.consumer or not self.config.consumer.topic_or_queue:
            logger.warning(f"[{self.name}] Consumer broker or topic_or_queue not configured.")
            return

        yield from self.consumer_broker.consume(
            topic_or_queue=self.config.consumer.topic_or_queue,
            exchange_or_group=self.config.consumer.exchange,
        )

    def send_output_message(self, result: OutputT) -> None:
        """Publish processing output to the producer broker."""
        if not self.producer_broker or not self.config.producer or not self.config.producer.topic_or_queue:
            logger.warning(f"[{self.name}] Output generated, but producer broker or destination is not configured.")
            return

        try:
            payload_data = result.model_dump(by_alias=True) if isinstance(result, BaseModel) else result
            self.producer_broker.publish(
                topic_or_queue=self.config.producer.topic_or_queue,
                message=payload_data,
                exchange_or_group=self.config.producer.exchange or "",
            )
        except Exception as exc:
            logger.error(f"[{self.name}] Error publishing output message: {exc}", exc_info=True)

    def run(self) -> None:
        """Worker loop entrypoint executed in the background thread."""
        logger.info(f"Worker thread '{self.name}' started.")
        self._init_brokers()

        # If no consumer is configured, sub-classes (like producers) handle their own loop
        if not self.config.consumer:
            logger.info(f"Worker thread '{self.name}' has no consumer configured.")
            return

        for raw_message in self.read_raw_message():
            if not self._is_running:
                logger.info(f"Worker thread '{self.name}' stopping...")
                break

            if raw_message is None:
                continue

            parsed_payload = self._parse_message(raw_message)
            if parsed_payload is None:
                continue

            try:
                result = self.process_payload(parsed_payload)
            except Exception as proc_err:
                logger.error(f"Processing error in worker '{self.name}': {proc_err}")
                self.handle_processing_error(parsed_payload, proc_err)
                continue

            if result is not None:
                self.send_output_message(result)

        logger.info(f"Worker thread '{self.name}' stopped.")

    def _parse_message(self, raw_message: Any) -> PayloadT | None:
        """Parse raw broker bytes or strings into the target Pydantic model."""
        if self.payload_model is None:
            return raw_message  # type: ignore

        try:
            if isinstance(raw_message, (str, bytes)):
                data_dict: dict[str, Any] = json.loads(raw_message)
            elif isinstance(raw_message, dict):
                data_dict = raw_message
            else:
                raise ValueError(f"Unsupported payload type: {type(raw_message)}")

            return self.payload_model.model_validate(data_dict)

        except (json.JSONDecodeError, ValidationError, ValueError) as err:
            logger.warning(f"[{self.name}] Schema validation failed for incoming message.")
            if not isinstance(err, ValidationError):
                err = ValidationError.from_exception_data(
                    title=self.payload_model.__name__,
                    line_errors=[],
                )
            self.handle_validation_error(raw_message, err)
            return None

    def _publish_to_dlq(self, payload: Any, error: Exception, reason: str) -> None:
        """Publish error envelope to the error broker."""
        if not self.error_broker or not self.config.error or not self.config.error.topic_or_queue:
            logger.warning(f"[{self.name}] Failed to dispatch error: DLQ broker destination not configured.")
            return

        try:
            error_event = ErrorEnvelope(
                failed_payload=payload,
                error_type=f"{reason}: {type(error).__name__}",
                error_message=str(error),
                traceback=traceback.format_exc(),
            )
            self.error_broker.publish(
                topic_or_queue=self.config.error.topic_or_queue,
                message=error_event.model_dump(by_alias=True),
                exchange_or_group=self.config.error.exchange or "",
            )
            logger.info(f"[{self.name}] Message successfully routed to DLQ '{self.config.error.topic_or_queue}'.")
        except Exception as dlq_err:
            logger.critical(f"[{self.name}] Critical failure sending message to DLQ: {dlq_err}")