"""Unit tests for the MessageBrokerFactory class.

This module verifies the correct behavior of the MessageBrokerFactory,
ensuring it instantiates the correct broker adapters based on the provided
BrokersEnum values, passes keyword arguments properly, and raises
BrokerNotFoundError for unsupported or invalid broker types.
"""

import unittest
from unittest.mock import MagicMock, patch

from event_driven.infrastructure.config.enumerations.brokers import BrokersEnum
from event_driven.infrastructure.exceptions.exceptions import BrokerNotFoundError

# Import factory, enum, and exception according to your project structure
from event_driven.infrastructure.messaging.broker_factory import MessageBrokerFactory


class TestMessageBrokerFactory(unittest.TestCase):
    """Test suite for MessageBrokerFactory creation logic."""

    @patch("event_driven.infrastructure.messaging.broker_factory.KafkaAdapter")
    def test_create_kafka_broker(self, mock_kafka_adapter: MagicMock) -> None:
        """Verify that KafkaAdapter is correctly instantiated with the provided keyword arguments."""
        # Arrange: Setup mock instance return value
        mock_instance = MagicMock()
        mock_kafka_adapter.return_value = mock_instance

        # Act: Call the factory method for Kafka
        result = MessageBrokerFactory.create_broker(BrokersEnum.KAFKA, host="localhost", port=9092)

        # Assert: Verify adapter was initialized with correct arguments and returned
        mock_kafka_adapter.assert_called_once_with(host="localhost", port=9092)
        self.assertEqual(result, mock_instance)

    @patch("event_driven.infrastructure.messaging.broker_factory.LocalQueueAdapter")
    def test_create_local_broker(self, mock_local_adapter: MagicMock) -> None:
        """Verify that LocalQueueAdapter is correctly instantiated."""
        # Arrange: Setup mock instance return value
        mock_instance = MagicMock()
        mock_local_adapter.return_value = mock_instance

        # Act: Call the factory method for Local queue
        result = MessageBrokerFactory.create_broker(BrokersEnum.LOCAL)

        # Assert: Verify adapter was initialized without arguments and returned
        mock_local_adapter.assert_called_once_with()
        self.assertEqual(result, mock_instance)

    @patch("event_driven.infrastructure.messaging.broker_factory.RabbitMQAdapter")
    def test_create_rabbitmq_broker(self, mock_rabbitmq_adapter: MagicMock) -> None:
        """Verify that RabbitMQAdapter is correctly instantiated with the provided keyword arguments."""
        # Arrange: Setup mock instance return value
        mock_instance = MagicMock()
        mock_rabbitmq_adapter.return_value = mock_instance

        # Act: Call the factory method for RabbitMQ
        result = MessageBrokerFactory.create_broker(BrokersEnum.RABBITMQ, url="amqp://guest:guest@localhost/")

        # Assert: Verify adapter was initialized with correct arguments and returned
        mock_rabbitmq_adapter.assert_called_once_with(url="amqp://guest:guest@localhost/")
        self.assertEqual(result, mock_instance)

    def test_create_broker_raises_not_found_error_for_invalid_type(self) -> None:
        """Verify that BrokerNotFoundError is raised when an unsupported or invalid broker type is passed."""
        # Arrange: Use an unsupported or fake enum value
        invalid_broker_type = MagicMock()

        # Act & Assert: Verify the custom exception is raised
        with self.assertRaises(BrokerNotFoundError):
            MessageBrokerFactory.create_broker(invalid_broker_type)  # type: ignore


if __name__ == "__main__":
    unittest.main()
