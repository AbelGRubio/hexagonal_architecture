from event_driven.infrastructure.config.enumerations.brokers import BrokersEnum
from event_driven.infrastructure.exceptions.exceptions import BrokerNotFoundError

from .brokers import IMessageBroker, KafkaAdapter, LocalQueueAdapter, RabbitMQAdapter


class MessageBrokerFactory:
    """Fábrica para instanciar el broker deseado según la configuración."""

    @staticmethod
    def create_broker(broker_type: BrokersEnum, **kwargs) -> IMessageBroker:
        """Create a broker."""
        brokers_ = {
            BrokersEnum.KAFKA: KafkaAdapter,
            BrokersEnum.LOCAL: LocalQueueAdapter,
            BrokersEnum.RABBITMQ: RabbitMQAdapter,
        }

        res_ = brokers_.get(broker_type)

        if not res_:
            raise BrokerNotFoundError()

        return res_(**kwargs)
