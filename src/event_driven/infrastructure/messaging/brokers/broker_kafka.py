import orjson
from typing import Any, Optional

from confluent_kafka import Producer, Consumer
from .interface_message import IMessageBroker
from event_driven.logger import get_logger

logger = get_logger(__name__)

class KafkaAdapter(IMessageBroker):
    """Adaptador para Apache Kafka (usando confluent-kafka)."""

    def __init__(self, bootstrap_servers: str = "localhost:9092", group_id: str = "pyevoke-group"):
        self.bootstrap_servers = bootstrap_servers
        self.group_id = group_id

        # Configuración del Productor
        self.producer_config = {
            'bootstrap.servers': self.bootstrap_servers
        }
        self.producer = Producer(self.producer_config)

        # Diccionario para mantener consumidores activos por "topic"
        self.consumers: dict[str, Consumer] = {}

    def _get_or_create_consumer(self, topic: str) -> Consumer:
        if topic not in self.consumers:
            conf = {
                'bootstrap.servers': self.bootstrap_servers,
                'group.id': self.group_id,
                'auto.offset.reset': 'earliest',
                'enable.auto.commit': False  # Control manual del commit (equivalente al ACK)
            }
            consumer = Consumer(conf)
            consumer.subscribe([topic])
            self.consumers[topic] = consumer
        return self.consumers[topic]

    def publish(self, topic_or_queue: str, message: dict) -> None:
        """Publica un mensaje (evento) en un tópico de Kafka."""

        def delivery_report(err, msg):
            if err is not None:
                logger.error(f"[Kafka] Error al enviar mensaje: {err}")
            else:
                logger.info(f"[Kafka] Mensaje entregado a {msg.topic()} [{msg.partition()}]")

        self.producer.produce(
            topic=topic_or_queue,
            value=orjson.dumps(message).decode("utf-8"),
            callback=delivery_report
        )
        # Forzar el envío inmediato
        self.producer.poll(0)
        self.producer.flush()

    def consume(self, source: str) -> Optional[Any]:
        """Consume un mensaje de un tópico de Kafka con un timeout corto."""
        consumer = self._get_or_create_consumer(source)

        # timeout=1.0 segundo para no bloquear el hilo infinitamente y permitir pausas limpias
        msg = consumer.poll(timeout=1.0)

        if msg is None:
            return None
        if msg.error():
            print(f"[Kafka] Error en consumo: {msg.error()}")
            return None

        # Retornamos un diccionario con el valor y el objeto mensaje original (para hacer commit luego)
        return {
            "body": msg.value().decode('utf-8'),
            "raw_msg": msg,
            "consumer": consumer
        }

    def commit(self, consumer: Consumer, raw_msg: Any):
        """Equivalente al ACK: confirma que el mensaje fue procesado con éxito."""
        consumer.commit(message=raw_msg, asynchronous=False)