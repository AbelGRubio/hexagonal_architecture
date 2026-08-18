from .brokers import KafkaAdapter, RabbitMQAdapter, LocalQueueAdapter

class MessageBrokerFactory:
    """Fábrica para instanciar el broker deseado según la configuración."""

    @staticmethod
    def create_broker(broker_type: str, **kwargs) -> IMessageBroker:
        if broker_type == "queue":
            return LocalQueueAdapter()
        elif broker_type == "rabbitmq":
            host = kwargs.get("host", "localhost")
            return RabbitMQAdapter(host=host)
        elif broker_type == "kafka":
            return KafkaAdapter()
        else:
            raise ValueError(f"Tipo de broker desconocido: {broker_type}")
