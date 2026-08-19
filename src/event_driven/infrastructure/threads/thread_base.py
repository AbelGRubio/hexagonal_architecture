import abc
import json
import logging
import threading
from typing import Any, Generic, Optional, Type, TypeVar

from pydantic import BaseModel, ValidationError

# Configure logger
logger = logging.getLogger(__name__)

# Generic type variable bounded to Pydantic's BaseModel
PayloadT = TypeVar("PayloadT", bound=BaseModel)
OutputT = TypeVar("OutputT", bound=BaseModel)


class BaseWorkerThread(threading.Thread, abc.ABC, Generic[PayloadT, OutputT]):
    """
    Abstract base worker class executing in a dedicated thread.

    Handles the lifecycle of consuming raw messages, parsing and validating
    them into a strongly-typed Pydantic model, invoking business logic,
    and dispatching processing results or validation errors.
    """

    def __init__(
            self,
            schema_model: Type[PayloadT],
            name: Optional[str] = None,
            daemon: bool = True,
    ) -> None:
        """
        Initialize the base worker thread.

        :param schema_model: The Pydantic model class used for data validation.
        :param name: Optional name for the thread.
        :param daemon: Whether the thread runs as a daemon.
        """
        super().__init__(name=name, daemon=daemon)
        self.schema_model: Type[PayloadT] = schema_model
        self._is_running: bool = True

    def stop(self) -> None:
        """
        Gracefully stop the thread loop.
        """
        self._is_running = False

    # ------------------------------------------------------------------
    # ABSTRACT METHODS (Must be implemented by concrete classes)
    # ------------------------------------------------------------------

    @abc.abstractmethod
    def read_raw_message(self) -> Optional[Any]:
        """
        Fetch a raw message from the source queue (e.g., Kafka, RabbitMQ, or queue.Queue).

        Should return None if no message is available during the timeout period.
        """
        pass

    @abc.abstractmethod
    def process_payload(self, payload: PayloadT) -> Optional[OutputT]:
        """
        Execute core business logic on the validated Pydantic model.

        :param payload: Validated Pydantic model instance.
        :return: Processed output data to be dispatched, or None if no response is needed.
        """
        pass

    @abc.abstractmethod
    def send_output_message(self, result: OutputT) -> None:
        """
        Dispatch the processed result to the destination queue or topic.

        :param result: The output returned by `process_payload`.
        """
        pass

    @abc.abstractmethod
    def handle_validation_error(self, raw_message: Any, error: ValidationError) -> None:
        """
        Handle messages that failed Pydantic schema validation (e.g., send to Dead Letter Queue).

        :param raw_message: The original unparsed payload.
        :param error: The caught Pydantic ValidationError.
        """
        pass

    @abc.abstractmethod
    def handle_processing_error(self, payload: PayloadT, error: Exception) -> None:
        """
        Handle unhandled exceptions occurring inside `process_payload`.

        :param payload: The validated payload that caused the runtime error.
        :param error: The raised exception.
        """
        pass

    # ------------------------------------------------------------------
    # THREAD RUN LOOP & PARSING LOGIC
    # ------------------------------------------------------------------

    def run(self) -> None:
        """
        Main execution loop running in the separate thread.
        """
        logger.info(f"Worker thread '{self.name}' started.")

        while self._is_running:
            try:
                # 1. Fetch raw payload from source
                raw_message: Optional[Any] = self.read_raw_message()
                if raw_message is None:
                    continue

                # 2. Parse and validate against Pydantic schema
                parsed_payload: Optional[PayloadT] = self._parse_message(raw_message)
                if parsed_payload is None:
                    continue  # Validation failed; already handled by handle_validation_error

                # 3. Execute business logic
                try:
                    result: Optional[OutputT] = self.process_payload(parsed_payload)
                except Exception as proc_err:
                    logger.error(f"Processing error in thread '{self.name}': {proc_err}")
                    self.handle_processing_error(parsed_payload, proc_err)
                    continue

                # 4. Dispatch output if present
                if result is not None:
                    self.send_output_message(result)

            except Exception as unhandled_err:
                logger.critical(f"Unhandled error in thread '{self.name}': {unhandled_err}")

        logger.info(f"Worker thread '{self.name}' stopped.")

    def _parse_message(self, raw_message: Any) -> Optional[PayloadT]:
        """
        Convert raw payload (JSON string, bytes, or dict) into the Pydantic model instance.

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
            return self.schema_model.model_validate(data_dict)

        except (json.JSONDecodeError, ValidationError, ValueError) as err:
            logger.warning(f"Schema validation failed for incoming message in '{self.name}' thread.")

            if isinstance(err, ValidationError):
                self.handle_validation_error(raw_message, err)
            else:
                # Construct synthetic ValidationError for bad JSON / invalid structure
                synthetic_error = ValidationError.from_exception_data(
                    title=self.schema_model.__name__,
                    line_errors=[],
                )
                self.handle_validation_error(raw_message, synthetic_error)

            return None