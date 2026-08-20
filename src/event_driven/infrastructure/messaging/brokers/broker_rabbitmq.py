from typing import Any, Optional

import orjson
import pika

from .interface_message import IMessageBroker


class RabbitMQAdapter(IMessageBroker):
    """Adaptador para RabbitMQ (usando pika)."""

    def __init__(self, host: str = "localhost"):

        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host=host))
        self.channel = self.connection.channel()

    def publish(self, topic_or_queue: str, message: dict) -> None:
        self.channel.queue_declare(queue=topic_or_queue, durable=True)
        self.channel.basic_publish(
            exchange='',
            routing_key=topic_or_queue,
            body=orjson.dumps(message)
        )

    def consume(self, source: str, timeout: float = 1.0) -> Optional[Any]:
        # self.channel.queue_declare(queue=source, durable=True)
        # Nota: RabbitMQ en un hilo suele requerir callbacks,
        # pero para adaptarlo al bucle 'get' puedes usar basic_get:
        method_frame, header_frame, body = self.channel.basic_get(queue=source, auto_ack=False)
        if method_frame:
            # Guardamos el delivery_tag para hacer el ACK más tarde si es necesario
            return {"body": body, "delivery_tag": method_frame.delivery_tag}
        return None

    def ack(self, delivery_tag: int):
        self.channel.basic_ack(delivery_tag=delivery_tag)