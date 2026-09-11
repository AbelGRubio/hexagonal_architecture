"""Unit tests for the RabbitMQAdapter class.

This module verifies the correct connection initialization, publishing logic,
and consumption behavior of RabbitMQAdapter using mocks for pika and circuit breakers.
"""

from unittest.mock import MagicMock, patch
import pytest

# Patch broker_pybreaker at import time to avoid real Redis connections
# Wrap the import so the patch is active while the module initializes.
with patch("event_driven.infrastructure.config.init_pybreaker.broker_pybreaker") as mock_breaker:
    mock_breaker.return_value = lambda f: f
    from event_driven.infrastructure.messaging.brokers.broker_rabbitmq import RabbitMQAdapter


class TestRabbitMQAdapter:
    """Test suite for RabbitMQAdapter operations."""

    @patch("event_driven.infrastructure.messaging.brokers.broker_rabbitmq.pika.BlockingConnection")
    def test_init_success(self, mock_blocking_connection: MagicMock) -> None:
        """Verify that the adapter establishes a connection and opens a channel successfully on init."""
        mock_connection = MagicMock()
        mock_channel = MagicMock()
        mock_blocking_connection.return_value = mock_connection
        mock_connection.channel.return_value = mock_channel

        # Act: Instanciar el adaptador
        adapter = RabbitMQAdapter(host="testhost", port=5672)

        # Assert: Validar conexión y canal
        mock_blocking_connection.assert_called_once()
        mock_connection.channel.assert_called_once()
        assert adapter.connection == mock_connection
        assert adapter.channel == mock_channel

    @patch("event_driven.infrastructure.messaging.brokers.broker_rabbitmq.pika.BlockingConnection")
    def test_publish_success(self, mock_blocking_connection: MagicMock) -> None:
        """Verify that messages are successfully published to a queue."""
        mock_connection = MagicMock()
        mock_channel = MagicMock()
        mock_connection.is_closed = False
        mock_channel.is_closed = False
        mock_blocking_connection.return_value = mock_connection
        mock_connection.channel.return_value = mock_channel

        adapter = RabbitMQAdapter()

        # Act: Publicar mensaje
        message = {"event": "test_message"}
        adapter.publish(topic_or_queue="test_queue", message=message)

        # Assert: Comprobar que se declara la cola y se publica con basic_publish
        mock_channel.queue_declare.assert_called_once_with(queue="test_queue", durable=True)
        mock_channel.basic_publish.assert_called_once()

    @patch("event_driven.infrastructure.messaging.brokers.broker_rabbitmq.pika.BlockingConnection")
    def test_consume_success(self, mock_blocking_connection: MagicMock) -> None:
        """Verify that messages can be consumed via generator."""
        mock_connection = MagicMock()
        mock_channel = MagicMock()
        mock_connection.is_closed = False
        mock_channel.is_closed = False
        mock_blocking_connection.return_value = mock_connection
        mock_connection.channel.return_value = mock_channel

        # Simular marcos devueltos por el consumo de pika: (method_frame, properties, body)
        mock_method_frame = MagicMock()
        mock_method_frame.delivery_tag = 1
        mock_body = b'{"data": "test"}'

        mock_channel.consume.return_value = [(mock_method_frame, MagicMock(), mock_body)]

        adapter = RabbitMQAdapter()

        # Act: Consumir mensajes
        generator = adapter.consume(topic_or_queue="test_queue", timeout=1.0)
        messages = list(generator)

        # Assert: Validar flujo de consumo y acknowledgments
        mock_channel.basic_qos.assert_called_once_with(prefetch_count=1)
        mock_channel.queue_declare.assert_called_once_with(queue="test_queue", durable=True)
        mock_channel.basic_ack.assert_called_once_with(delivery_tag=1)
        assert len(messages) == 1
        assert messages[0] == mock_body