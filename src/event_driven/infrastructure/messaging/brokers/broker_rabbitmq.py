from typing import Any

import orjson
import pika

from .interface_message import IMessageBroker


class RabbitMQAdapter(IMessageBroker):
    """Adaptador para RabbitMQ (usando pika)."""

    def __init__(self, host: str = "localhost"):

        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host=host))
        self.channel = self.connection.channel()

    def publish(
        self,
        topic_or_queue: str,
        message: dict,
        exchange: str = "",
        routing_key: str | None = None,
    ) -> None:
        # Si no se pasa routing_key, se usa la cola por defecto
        rk = routing_key if routing_key is not None else topic_or_queue

        # Si publicas al default exchange (''), declaras la cola
        if exchange == "":
            self.channel.queue_declare(queue=topic_or_queue, durable=True)
        else:
            self.channel.exchange_declare(exchange=exchange, exchange_type="direct", durable=True)

        self.channel.basic_publish(exchange=exchange, routing_key=rk, body=orjson.dumps(message))

    def consume(
        self,
        source: str,
        timeout: float = 1.0,
        exchange: str | None = None,
        routing_key: str | None = None,
    ) -> Any | None:
        # 1. Asegurar que la cola existe
        self.channel.queue_declare(queue=source, durable=True)

        # 2. Si nos piden consumir de un Exchange específico, enlazamos la cola a dicho Exchange
        if exchange:
            # Declaramos el exchange (tipo direct o topic según tu arquitectura)
            self.channel.exchange_declare(exchange=exchange, exchange_type="direct", durable=True)

            # El binding mapea: Exchange + RoutingKey -> Cola (source)
            rk_to_bind = routing_key if routing_key is not None else source
            self.channel.queue_bind(queue=source, exchange=exchange, routing_key=rk_to_bind)

        # 3. Consumir de la cola asociada
        method_frame, header_frame, body = self.channel.basic_get(queue=source, auto_ack=False)
        if method_frame and body:
            return {
                "body": orjson.loads(body),
                "delivery_tag": method_frame.delivery_tag,
                "routing_key": method_frame.routing_key,
                "exchange": method_frame.exchange,
            }
        return None

    def ack(self, delivery_tag: int):
        self.channel.basic_ack(delivery_tag=delivery_tag)
