from typing import Any, Generator

import orjson
import pika

from .interface_message import IMessageBroker


class RabbitMQAdapter(IMessageBroker):
    """Adaptador para RabbitMQ (usando pika)."""

    def __init__(self, **kwargs):

        self.connection = pika.BlockingConnection(pika.ConnectionParameters(**kwargs))
        self.channel = self.connection.channel()

    def publish(
        self,
        topic_or_queue: str,
        message: dict,
        exchange_or_group: str = "",
    ) -> None:
        # Si no se pasa routing_key, se usa la cola por defecto
        rk = topic_or_queue

        # Si publicas al default exchange (''), declaras la cola
        if exchange_or_group == "":
            self.channel.queue_declare(queue=topic_or_queue, durable=True)
        else:
            self.channel.exchange_declare(exchange=exchange_or_group, exchange_type="direct", durable=True)

        self.channel.basic_publish(exchange=exchange_or_group, routing_key=rk, body=orjson.dumps(message))

    def consume(
        self,
        topic_or_queue: str,
        exchange_or_group: str | None = None,
        timeout: float = 1.0,
    ) -> Generator[Any, None, None]:
        # 1. Asegurar que la cola existe
        # 1. Control de flujo: Evita saturar la memoria entregando solo 1 mensaje no confirmado a la vez
        self.channel.basic_qos(prefetch_count=1)

        # 2. Asegurar que la cola existe
        self.channel.queue_declare(queue=topic_or_queue, durable=True)

        # 3. Vincular a Exchange si aplica
        if exchange_or_group:
            self.channel.exchange_declare(exchange=exchange_or_group, exchange_type="direct", durable=True)
            self.channel.queue_bind(queue=topic_or_queue, exchange=exchange_or_group, routing_key=topic_or_queue)

        # 4. Consumir de forma segura usando inactivity_timeout
        # pika devolverá (None, None, None) cuando venza el timeout sin mensajes
        try:
            for method_frame, properties, body in self.channel.consume(
                    queue=topic_or_queue,
                    auto_ack=False,
                    inactivity_timeout=timeout
            ):
                # Si expira el timeout y la cola estuvo vacía, entregamos (None, None)
                # Esto permite al Worker continuar su bucle 'while self._is_running' sin romper el socket
                if method_frame is None:
                    yield None, None
                    continue

                # Función para que el Worker haga el ACK al FINALizar su procesamiento
                def ack_callback():
                    self.channel.basic_ack(delivery_tag=method_frame.delivery_tag)

                yield body, ack_callback

        finally:
            # Cancela el consumidor en RabbitMQ cuando el generador se cierra
            self.channel.cancel()


    def ack(self, delivery_tag: int):
        self.channel.basic_ack(delivery_tag=delivery_tag)
