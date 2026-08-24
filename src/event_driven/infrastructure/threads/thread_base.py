import abc
import json
import logging
import threading
from typing import Any, Generic, Generator, TypeVar, Callable

from pydantic import BaseModel, ValidationError

from event_driven.infrastructure.messaging.brokers.interface_message import IMessageBroker

# Configure logger
logger = logging.getLogger(__name__)

# Generic type variable bounded to Pydantic's BaseModel
PayloadT = TypeVar("PayloadT", bound=BaseModel)
OutputT = TypeVar("OutputT", bound=BaseModel)


class BaseWorkerThread(threading.Thread, abc.ABC, Generic[PayloadT, OutputT]):
    """Abstract base worker class executing in a dedicated thread.

    Handles the lifecycle of consuming raw messages, parsing and validating
    them into a strongly-typed Pydantic model, invoking business logic,
    and dispatching processing results or validation errors.
    """

    def __init__(
        self,
        payload_model: type[PayloadT],
        broker: IMessageBroker,
        consume_destination: str,
        publish_destination: str | None = None,
        name: str | None = None,
        daemon: bool = True,
    ) -> None:
        """Initialize the base worker thread.

        :param payload_model: The Pydantic model class used for data validation.
        :param name: Optional name for the thread.
        :param daemon: Whether the thread runs as a daemon.
        """
        super().__init__(name=name, daemon=daemon)
        self.payload_model: type[PayloadT] = payload_model
        self.broker: IMessageBroker = broker
        self.consume_destination: str = consume_destination
        self.publish_destination: str | None = publish_destination
        self._is_running: bool = True

    def stop(self) -> None:
        """Gracefully stop the thread loop."""
        logger.info(f"Stop signal received '{self.name}'")
        self._is_running = False

    # ------------------------------------------------------------------
    # DEFAULT BROKER IMPLEMENTATIONS (Can be overridden if needed)
    # ------------------------------------------------------------------

    def read_raw_message(self) -> Generator[Any, Callable]:
        """Default implementation to fetch a raw message using the injected broker."""
        return self.broker.consume(self.consume_destination)


    def send_output_message(self, result: OutputT) -> None:
        """Default implementation to dispatch the processed result using the broker."""
        if self.publish_destination and self.broker:
            try:
                payload_str = str(result.model_dump_json())
                self.broker.publish(self.publish_destination, payload_str)
            except Exception as e:
                logger.error(f"Error publishing message from '{self.name}': {e}")
        else:
            logger.warning(f"[{self.name}] Output generated but no publish_destination or broker configured.")

    # ------------------------------------------------------------------
    # ABSTRACT METHODS (Must be implemented by concrete classes)
    # ------------------------------------------------------------------

    @abc.abstractmethod
    def process_payload(self, payload: PayloadT) -> OutputT | None:
        """Execute core business logic on the validated Pydantic model.

        :param payload: Validated Pydantic model instance.
        :return: Processed output data to be dispatched, or None if no response is needed.
        """
        pass

    @abc.abstractmethod
    def handle_validation_error(self, raw_message: Any, error: ValidationError) -> None:
        """Handle messages that failed Pydantic schema validation (e.g., send to Dead Letter Queue).

        :param raw_message: The original unparsed payload.
        :param error: The caught Pydantic ValidationError.
        """
        pass

    @abc.abstractmethod
    def handle_processing_error(self, payload: PayloadT, error: Exception) -> None:
        """Handle unhandled exceptions occurring inside `process_payload`.

        :param payload: The validated payload that caused the runtime error.
        :param error: The raised exception.
        """
        pass

    # ------------------------------------------------------------------
    # THREAD RUN LOOP & PARSING LOGIC
    # ------------------------------------------------------------------

    def run(self) -> None:
        """Main execution loop running in the separate thread."""
        logger.info(f"Worker thread '{self.name}' started.")

        # El broker decide cómo bloquear y entregar cada mensaje
        for raw_message, ack in self.read_raw_message():
            if not self._is_running:
                logger.info(f"Signal received from thread '{self.name}' stopped. State {self._is_running}")
                break

            if raw_message is None:
                logger.info(f"Waiting for the item to process. { self._is_running}")
                continue

            parsed_payload = self._parse_message(raw_message)
            if parsed_payload is None:
                continue

            try:
                result = self.process_payload(parsed_payload)
                ack()
            except Exception as proc_err:
                logger.error(f"Processing error in thread '{self.name}': {proc_err}")
                self.handle_processing_error(parsed_payload, proc_err)
                continue

            if result is not None:
                self.send_output_message(result)

        logger.info(f"Worker thread '{self.name}' stopped.")

    def _parse_message(self, raw_message: Any) -> PayloadT | None:
        """Convert raw payload (JSON string, bytes, or dict) into the Pydantic model instance.

        :param raw_message: Raw message object.
        :return: Validated PayloadT instance, or None if parsing fails.
        """
        try:
            if isinstance(raw_message, (str, bytes)):
                data_dict: dict[str, Any] = json.loads(raw_message)
            elif isinstance(raw_message, dict):
                data_dict = raw_message
            else:
                raise ValueError(f"Unsupported payload type: {type(raw_message)}")

            # Validate payload using Pydantic model
            return self.payload_model.model_validate(data_dict)

        except (json.JSONDecodeError, ValidationError, ValueError) as err:
            logger.warning(f"Schema validation failed for incoming message in '{self.name}' thread.")

            if isinstance(err, ValidationError):
                self.handle_validation_error(raw_message, err)
            else:
                # Construct synthetic ValidationError for bad JSON / invalid structure
                synthetic_error = ValidationError.from_exception_data(
                    title=self.payload_model.__name__,
                    line_errors=[],
                )
                self.handle_validation_error(raw_message, synthetic_error)

            return None
