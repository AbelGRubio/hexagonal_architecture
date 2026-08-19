from event_driven.infrastructure.config.enum.brokers import Broker
from .brokers import KafkaAdapter, RabbitMQAdapter, LocalQueueAdapter, IMessageBroker


class MessageBrokerFactory:
    """Fábrica para instanciar el broker deseado según la configuración."""

    @staticmethod
    def create_broker(broker_type: Broker, **kwargs) -> IMessageBroker:
        if broker_type == Broker.KAFKA:
            return LocalQueueAdapter()
        elif broker_type == Broker.RABBITMQ:
            host = kwargs.get("host", "localhost")
            return RabbitMQAdapter(host=host)
        elif broker_type == Broker.KAFKA:
            return KafkaAdapter()
        else:
            raise ValueError(f"Tipo de broker desconocido: {broker_type}")
