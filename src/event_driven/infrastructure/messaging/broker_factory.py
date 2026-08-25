"""Factory for creating configured message broker adapters.

This module centralizes broker creation and resolves the correct implementation
based on the enum value provided by the application configuration.
"""

from event_driven.infrastructure.config.enumerations.brokers import BrokersEnum
from event_driven.infrastructure.exceptions.exceptions import BrokerNotFoundError

from .brokers import IMessageBroker, KafkaAdapter, LocalQueueAdapter, RabbitMQAdapter


class MessageBrokerFactory:
    """Factory that instantiates the appropriate broker adapter for the project."""

    @staticmethod
    def create_broker(broker_type: BrokersEnum, **kwargs: object) -> IMessageBroker:
        """Create and return the broker adapter matching the requested type.

        Args:
            broker_type: Enumeration value indicating the desired broker.
            **kwargs: Additional configuration values passed to the adapter.

        Returns:
            A concrete broker instance implementing the shared messaging contract.

        Raises:
            BrokerNotFoundError: If the requested broker type is not supported.
        """
        brokers_ = {
            BrokersEnum.KAFKA: KafkaAdapter,
            BrokersEnum.LOCAL: LocalQueueAdapter,
            BrokersEnum.RABBITMQ: RabbitMQAdapter,
        }

        res_ = brokers_.get(broker_type)

        if not res_:
            raise BrokerNotFoundError()

        return res_(**kwargs)
