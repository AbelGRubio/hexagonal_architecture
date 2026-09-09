"""Unit tests for the base worker thread infrastructure module.

This test suite covers thread initialization, broker wiring, message consumption,
payload validation, processing error handling, and routing failed events to the DLQ.
"""

import json
from collections.abc import Generator
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from pydantic import BaseModel

from event_driven.infrastructure.config.schemas import BrokerConfigModel, ThreadConfigModel
from event_driven.infrastructure.threads.thread_base import BaseWorkerThread, ErrorEnvelope


# ==========================================
# Test Concrete Models & Implementations
# ==========================================

class SampleInput(BaseModel):
    """Sample input payload model for testing."""

    id: int
    name: str


class SampleOutput(BaseModel):
    """Sample output payload model for testing."""

    status: str
    result_id: int


class DummyWorkerThread(BaseWorkerThread[SampleInput, SampleOutput]):
    """Concrete implementation of BaseWorkerThread for unit testing."""

    def __init__(
        self,
        config: ThreadConfigModel,
        payload_model: type[SampleInput] | None = SampleInput,
        daemon: bool = True,
    ) -> None:
        """Initialize worker instance with test options."""
        super().__init__(config=config, payload_model=payload_model, daemon=daemon)
        self.processed_payloads: list[SampleInput] = []
        self.should_raise: bool = False

    def process_payload(self, payload: SampleInput) -> SampleOutput | None:
        """Process payload or simulate an unhandled failure."""
        if self.should_raise:
            raise RuntimeError("Processing failed catastrophically")
        self.processed_payloads.append(payload)
        return SampleOutput(status="PROCESSED", result_id=payload.id)


# ==========================================
# Fixtures
# ==========================================

@pytest.fixture
def mock_broker() -> MagicMock:
    """Provide a generic mock message broker."""
    broker: MagicMock = MagicMock()
    broker.consume.return_value = []
    return broker


@pytest.fixture
def thread_config() -> ThreadConfigModel:
    """Provide a standard ThreadConfigModel with consumer, producer, and error endpoints."""
    return ThreadConfigModel(
        name="inventory",
        consumer=BrokerConfigModel(
            broker_type="kafka",
            topic_or_queue="input_queue",
            exchange="test_exchange",
        ),
        producer=BrokerConfigModel(
            broker_type="kafka",
            topic_or_queue="output_queue",
            exchange="test_exchange",
        ),
        error=BrokerConfigModel(
            broker_type="kafka",
            topic_or_queue="error_dlq",
            exchange="test_exchange",
        ),
    )


# ==========================================
# 1. Thread & Broker Initialization Tests
# ==========================================

def test_worker_thread_init_defaults(thread_config: ThreadConfigModel) -> None:
    """Verify worker thread default properties and thread configuration setting."""
    worker: DummyWorkerThread = DummyWorkerThread(config=thread_config)

    assert worker.name == "inventory"
    assert worker.daemon is True
    assert worker._is_running is True
    assert worker.consumer_broker is None
    assert worker.producer_broker is None
    assert worker.error_broker is None


@patch("event_driven.infrastructure.threads.thread_base.MessageBrokerFactory")
def test_init_brokers_creates_configured_brokers(
    mock_factory_cls: MagicMock,
    thread_config: ThreadConfigModel,
) -> None:
    """Verify thread instantiates consumer, producer, and error brokers via factory."""
    factory_instance: MagicMock = MagicMock()
    mock_factory_cls.return_value = factory_instance

    worker: DummyWorkerThread = DummyWorkerThread(config=thread_config)
    worker._init_brokers()

    assert factory_instance.create_broker.call_count == 3
    assert worker.consumer_broker is not None
    assert worker.producer_broker is not None
    assert worker.error_broker is not None


# ==========================================
# 2. Parsing & Validation Tests
# ==========================================

def test_parse_message_valid_json_string(thread_config: ThreadConfigModel) -> None:
    """Verify _parse_message successfully parses a valid JSON string."""
    worker: DummyWorkerThread = DummyWorkerThread(config=thread_config)
    raw_json: str = json.dumps({"id": 101, "name": "Item A"})

    result: SampleInput | None = worker._parse_message(raw_json)

    assert result is not None
    assert isinstance(result, SampleInput)
    assert result.id == 101
    assert result.name == "Item A"


def test_parse_message_valid_dict(thread_config: ThreadConfigModel) -> None:
    """Verify _parse_message successfully processes a pre-parsed dictionary."""
    worker: DummyWorkerThread = DummyWorkerThread(config=thread_config)
    dict_payload: dict[str, Any] = {"id": 102, "name": "Item B"}

    result: SampleInput | None = worker._parse_message(dict_payload)

    assert result is not None
    assert result.id == 102


def test_parse_message_without_payload_model(thread_config: ThreadConfigModel) -> None:
    """Verify raw message is returned untouched when payload_model is None."""
    worker: DummyWorkerThread = DummyWorkerThread(config=thread_config, payload_model=None)
    raw_data: str = "raw_unstructured_string"

    result: Any = worker._parse_message(raw_data)

    assert result == "raw_unstructured_string"


def test_parse_message_invalid_schema_triggers_dlq(
    thread_config: ThreadConfigModel,
    mock_broker: MagicMock,
) -> None:
    """Verify schema mismatch routes failure message to DLQ and returns None."""
    worker: DummyWorkerThread = DummyWorkerThread(config=thread_config)
    worker.error_broker = mock_broker
    invalid_json: str = json.dumps({"id": "not_an_int", "name": "Item C"})

    result: SampleInput | None = worker._parse_message(invalid_json)

    assert result is None
    mock_broker.publish.assert_called_once()
    published_args: dict[str, Any] = mock_broker.publish.call_args.kwargs
    assert published_args["topic_or_queue"] == "error_dlq"
    assert "Validation Error" in published_args["message"]["error_type"]


def test_parse_message_unsupported_type_triggers_dlq(
    thread_config: ThreadConfigModel,
    mock_broker: MagicMock,
) -> None:
    """Verify unsupported data types trigger error handler and DLQ routing."""
    worker: DummyWorkerThread = DummyWorkerThread(config=thread_config)
    worker.error_broker = mock_broker

    result: SampleInput | None = worker._parse_message(12345)  # Integers are not supported raw input

    assert result is None
    mock_broker.publish.assert_called_once()


# ==========================================
# 3. Message Publishing & DLQ Tests
# ==========================================

def test_send_output_message_success(
    thread_config: ThreadConfigModel,
    mock_broker: MagicMock,
) -> None:
    """Verify output payload model is serialized and published correctly."""
    worker: DummyWorkerThread = DummyWorkerThread(config=thread_config)
    worker.producer_broker = mock_broker

    output: SampleOutput = SampleOutput(status="SUCCESS", result_id=200)
    worker.send_output_message(output)

    mock_broker.publish.assert_called_once_with(
        topic_or_queue="output_queue",
        message={"status": "SUCCESS", "result_id": 200},
        exchange_or_group="test_exchange",
    )


def test_send_output_message_unconfigured_producer_logs_warning(
    thread_config: ThreadConfigModel,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Verify output publication without configured producer aborts safely with warning."""
    worker: DummyWorkerThread = DummyWorkerThread(config=thread_config)
    worker.producer_broker = None

    output: SampleOutput = SampleOutput(status="SUCCESS", result_id=200)
    worker.send_output_message(output)

    assert "producer broker or destination is not configured" in caplog.text


def test_publish_to_dlq_formats_envelope(
    thread_config: ThreadConfigModel,
    mock_broker: MagicMock,
) -> None:
    """Verify _publish_to_dlq constructs ErrorEnvelope and dispatches error event."""
    worker: DummyWorkerThread = DummyWorkerThread(config=thread_config)
    worker.error_broker = mock_broker

    error: ValueError = ValueError("Bad parameter")
    worker._publish_to_dlq(payload={"key": "val"}, error=error, reason="Test Reason")

    mock_broker.publish.assert_called_once()
    call_kwargs: dict[str, Any] = mock_broker.publish.call_args.kwargs
    payload_sent: dict[str, Any] = call_kwargs["message"]

    assert payload_sent["failed_payload"] == {"key": "val"}
    assert payload_sent["error_type"] == "Test Reason: ValueError"
    assert payload_sent["error_message"] == "Bad parameter"
    assert "traceback" in payload_sent


def test_publish_to_dlq_handles_broker_exception(
    thread_config: ThreadConfigModel,
    mock_broker: MagicMock,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Verify critical failures during DLQ dispatch are trapped without raising unhandled exceptions."""
    mock_broker.publish.side_effect = Exception("DLQ Network Error")
    worker: DummyWorkerThread = DummyWorkerThread(config=thread_config)
    worker.error_broker = mock_broker

    worker._publish_to_dlq(payload={}, error=Exception("Original"), reason="Reason")

    assert "Critical failure sending message to DLQ" in caplog.text


# ==========================================
# 4. Worker Loop Execution Tests
# ==========================================

def test_run_without_consumer_stops_immediately(
    thread_config: ThreadConfigModel,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Verify worker with no consumer configuration terminates loop early."""
    thread_config.consumer = None
    worker: DummyWorkerThread = DummyWorkerThread(config=thread_config)

    with patch.object(worker, "_init_brokers"):
        worker.run()

    assert "" in caplog.text


def test_run_loop_processes_messages_and_produces_output(
    thread_config: ThreadConfigModel,
    mock_broker: MagicMock,
) -> None:
    """Verify full end-to-end execution loop: consuming, processing, and publishing output."""
    worker: DummyWorkerThread = DummyWorkerThread(config=thread_config)

    raw_msg_1: str = json.dumps({"id": 1, "name": "First"})
    raw_msg_2: str = json.dumps({"id": 2, "name": "Second"})

    mock_consumer: MagicMock = MagicMock()
    mock_consumer.consume.return_value = [raw_msg_1, raw_msg_2]
    mock_producer: MagicMock = MagicMock()

    with patch.object(worker, "broker_factory") as mock_factory:
        mock_factory.create_broker.side_effect = [mock_consumer, mock_producer, MagicMock()]
        worker.run()

    assert len(worker.processed_payloads) == 2
    assert mock_producer.publish.call_count == 2


def test_run_loop_stops_on_stop_signal(
    thread_config: ThreadConfigModel,
) -> None:
    """Verify worker loop breaks execution when stop() flag is set."""
    worker: DummyWorkerThread = DummyWorkerThread(config=thread_config)

    def msg_generator() -> Generator[str, None, None]:
        yield json.dumps({"id": 1, "name": "First"})
        worker.stop()
        yield json.dumps({"id": 2, "name": "Second"})

    mock_consumer: MagicMock = MagicMock()
    mock_consumer.consume.return_value = msg_generator()

    with patch.object(worker, "broker_factory") as mock_factory:
        mock_factory.create_broker.return_value = mock_consumer
        worker.run()

    assert len(worker.processed_payloads) == 1


def test_run_loop_handles_processing_exception(
    thread_config: ThreadConfigModel,
) -> None:
    """Verify unhandled processing exception is caught and dispatched to DLQ."""
    worker: DummyWorkerThread = DummyWorkerThread(config=thread_config)
    worker.should_raise = True

    raw_msg: str = json.dumps({"id": 10, "name": "Error Item"})

    mock_consumer: MagicMock = MagicMock()
    mock_consumer.consume.return_value = [raw_msg]
    mock_error_broker: MagicMock = MagicMock()

    with patch.object(worker, "broker_factory") as mock_factory:
        mock_factory.create_broker.side_effect = [mock_consumer, MagicMock(), mock_error_broker]
        worker.run()

    mock_error_broker.publish.assert_called_once()
    published_message: dict[str, Any] = mock_error_broker.publish.call_args.kwargs["message"]
    assert "Processing Error" in published_message["error_type"]
    assert published_message["failed_payload"] == {"id": 10, "name": "Error Item"}


def test_read_raw_message_unconfigured_consumer_returns_empty(
    thread_config: ThreadConfigModel,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Verify read_raw_message returns empty generator and logs warning if consumer is unconfigured."""
    worker: DummyWorkerThread = DummyWorkerThread(config=thread_config)
    worker.consumer_broker = None

    messages: list[Any] = list(worker.read_raw_message())

    assert len(messages) == 0
    assert "Consumer broker or topic_or_queue not configured" in caplog.text