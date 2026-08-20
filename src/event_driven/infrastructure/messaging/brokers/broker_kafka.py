from typing import Any, Optional
import orjson
from confluent_kafka import Consumer, Producer

from event_driven.logger import get_logger
from .interface_message import IMessageBroker

logger = get_logger(__name__)


class KafkaAdapter(IMessageBroker):
    """Adaptador para Apache Kafka (usando confluent-kafka)."""

    def __init__(
        self,
        bootstrap_servers: str = "localhost:9092",
        group_id: str = "pyevoke-group",
    ):
        self.bootstrap_servers = bootstrap_servers
        self.group_id = group_id

        # Configuración del Productor
        self.producer_config = {"bootstrap.servers": self.bootstrap_servers}
        self.producer = Producer(self.producer_config)

        # Diccionario para mantener consumidores activos por "topic"
        self.consumers: dict[str, Consumer] = {}

    def _get_or_create_consumer(self, topic: str) -> Consumer:
        if topic not in self.consumers:
            conf = {
                "bootstrap.servers": self.bootstrap_servers,
                "group.id": self.group_id,
                "auto.offset.reset": "earliest",
                "enable.auto.commit": False,  # Control manual del commit (ACK)
            }
            consumer = Consumer(conf)
            consumer.subscribe([topic])
            self.consumers[topic] = consumer
        return self.consumers[topic]

    def publish(
        self,
        topic_or_queue: str,
        message: dict,
        exchange: str = "",
        routing_key: Optional[str] = None,
    ) -> None:
        """Publica un mensaje en un tópico de Kafka.

        Los parámetros 'exchange' y 'routing_key' se ignoran ya que Kafka no usa
        esos conceptos.
        """

        def delivery_report(err, msg):
            if err is not None:
                logger.error(f"[Kafka] Error al enviar mensaje: {err}")
            else:
                logger.info(
                    f"[Kafka] Mensaje entregado a {msg.topic()} [{msg.partition()}]"
                )

        self.producer.produce(
            topic=topic_or_queue,
            value=orjson.dumps(message),
            callback=delivery_report,
        )
        # Forzar el envío inmediato
        self.producer.poll(0)
        self.producer.flush()

    def consume(
        self,
        source: str,
        timeout: float = 1.0,
        exchange: Optional[str] = None,
        routing_key: Optional[str] = None,
    ) -> Optional[Any]:
        """Consume un mensaje de un tópico de Kafka.

        Los parámetros 'exchange' y 'routing_key' se ignoran.
        """
        consumer = self._get_or_create_consumer(source)

        msg = consumer.poll(timeout=timeout)

        if msg is None:
            return None
        if msg.error():
            logger.error(f"[Kafka] Error en consumo: {msg.error()}")
            return None

        # Deserializamos el cuerpo directamente con orjson
        body = orjson.loads(msg.value())

        return {
            "body": body,
            "raw_msg": msg,
            "consumer": consumer,
        }

    def commit(self, consumer: Consumer, raw_msg: Any) -> None:
        """Equivalente al ACK: confirma que el mensaje fue procesado con éxito."""
        consumer.commit(message=raw_msg, asynchronous=False)