from typing import Any, Generator

import orjson
from confluent_kafka import Consumer, Producer

from event_driven.logger import get_logger

from .interface_message import IMessageBroker

logger = get_logger(__name__)


class KafkaAdapter(IMessageBroker):
    """Adaptador para Apache Kafka (usando confluent-kafka)."""

    DEFAULT_PRODUCER_CONFIG = {
        "bootstrap.servers": "localhost:9092",
        "acks": "all",
        "retries": 3,
        "compression.type": "snappy",
        "queue.buffering.max.messages": 100000,
    }

    def __init__(self, **kwargs):

        final_config = self.DEFAULT_PRODUCER_CONFIG.copy()
        if len(kwargs) > 0:
            final_config.update(kwargs)

        self.bootstrap_servers = final_config["bootstrap.servers"]

        # Configuración del Productor
        self.producer_config = final_config
        self.producer = Producer(self.producer_config)

        # Diccionario para mantener consumidores activos por "topic"
        self.consumers: dict[str, Consumer] = {}

    def _get_or_create_consumer(self, topic: str, exchange_or_group: str | None = '') -> Consumer:
        if topic not in self.consumers:
            conf = {
                "bootstrap.servers": self.bootstrap_servers,
                "group.id": exchange_or_group or 'kafka-group-infra',
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
        exchange_or_group: str = "",
    ) -> None:
        """Publica un mensaje en un tópico de Kafka.

        Los parámetros 'exchange' y 'routing_key' se ignoran ya que Kafka no usa
        esos conceptos.
        """

        def delivery_report(err, msg):
            if err is not None:
                logger.error(f"[Kafka] Error al enviar mensaje: {err}")
            else:
                logger.info(f"[Kafka] Mensaje entregado a {msg.topic()} [{msg.partition()}]")

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
        topic_or_queue: str,
        exchange_or_group: str | None = None,
        timeout: float = 1.0,
    ) -> Generator[Any, None, None]:
        """Consume un mensaje de un tópico de Kafka.

        Los parámetros 'exchange' y 'routing_key' se ignoran.
        """
        consumer = self._get_or_create_consumer(topic_or_queue, exchange_or_group=exchange_or_group)

        msg = consumer.poll(timeout=timeout)

        if msg is None:
            return None, None
        if msg.error():
            logger.error(f"[Kafka] Error en consumo: {msg.error()}")
            return None, None

        return orjson.loads(msg.value()), None

    def commit(self, consumer: Consumer, raw_msg: Any) -> None:
        """Equivalente al ACK: confirma que el mensaje fue procesado con éxito."""
        consumer.commit(message=raw_msg, asynchronous=False)
