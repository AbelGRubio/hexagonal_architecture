from event_driven.infrastructure.config.enum.brokers import Broker
from .brokers import KafkaAdapter, RabbitMQAdapter, LocalQueueAdapter, IMessageBroker
from event_driven.infrastructure.exceptions.exceptions import BrokerNotFoundError

class MessageBrokerFactory:
    """Fábrica para instanciar el broker deseado según la configuración."""

    @staticmethod
    def create_broker(broker_type: Broker, **kwargs) -> IMessageBroker:
        """Create a broker. """
        brokers_ = {
            Broker.KAFKA: KafkaAdapter,
            Broker.LOCAL: LocalQueueAdapter,
            Broker.RABBITMQ: RabbitMQAdapter,
        }

        res_ = brokers_.get(broker_type, None)

        if not res_:
            raise BrokerNotFoundError()

        return res_(**kwargs)
