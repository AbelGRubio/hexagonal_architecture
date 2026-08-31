"""RabbitMQ broker adapter implementation.

This module provides a concrete adapter for RabbitMQ using the pika client.
"""

import os
from typing import Any, Generator

import orjson
import pika

from .interface_message import IMessageBroker


class RabbitMQAdapter(IMessageBroker):
    """RabbitMQ adapter implementation using pika."""

    DEFAULT_PARAMS = {
        "host": "localhost",
        "port": 5672,
        "heartbeat": 600,
        "blocked_connection_timeout": 300,
    }

    def __init__(self, **kwargs: Any) -> None:
        """Create a blocking RabbitMQ connection and open its channel."""
        connection_params = self._get_default_params()

        if "username" in kwargs and "password" in kwargs:
            kwargs["credentials"] = pika.PlainCredentials(
                kwargs.pop("username"),
                kwargs.pop("password")
            )

        connection_params |= kwargs
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(**connection_params))
        self.channel = self.connection.channel()

    def publish(
        self,
        topic_or_queue: str,
        message: dict[str, Any],
        exchange_or_group: str = "",
    ) -> None:
        """Publish a message to a RabbitMQ queue or exchange.

        Args:
            topic_or_queue: Queue name used as routing key when using the default
                exchange, or the target queue name for direct bindings.
            message: Message payload to serialize and send.
            exchange_or_group: Exchange name when a named exchange is used.
        """
        rk = topic_or_queue

        # If publishing to the default exchange, declare the queue.
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
        """Consume messages from a RabbitMQ queue.

        Args:
            topic_or_queue: Queue name to consume from.
            exchange_or_group: Optional exchange name to bind to the queue.
            timeout: Maximum time to wait for a message before returning.

        Yields:
            The next message body if one is available; otherwise, the generator
            will terminate its current iteration after the inactivity timeout.
        """
        self.channel.basic_qos(prefetch_count=1)
        self.channel.queue_declare(queue=topic_or_queue, durable=True)

        if exchange_or_group:
            self.channel.exchange_declare(exchange=exchange_or_group, exchange_type="direct", durable=True)
            self.channel.queue_bind(queue=topic_or_queue, exchange=exchange_or_group, routing_key=topic_or_queue)

        try:
            for method_frame, properties, body in self.channel.consume(
                queue=topic_or_queue,
                auto_ack=False,
                inactivity_timeout=timeout,
            ):
                if method_frame is None:
                    yield None
                    continue

                self.channel.basic_ack(delivery_tag=method_frame.delivery_tag)
                yield body

        finally:
            self.channel.cancel()

    def ack(self, delivery_tag: int) -> None:
        """Acknowledge a specific message delivery tag in RabbitMQ."""
        self.channel.basic_ack(delivery_tag=delivery_tag)

    def _get_default_params(self) -> dict[str, Any]:
        """Load default parameters combining class defaults and environment variables."""
        params: dict[str, Any] = {
            "host": os.getenv("RABBITMQ_HOST", self.DEFAULT_PARAMS["host"]),
            "port": int(os.getenv("RABBITMQ_PORT", self.DEFAULT_PARAMS["port"])),
            "heartbeat": int(os.getenv("RABBITMQ_HEARTBEAT", self.DEFAULT_PARAMS["heartbeat"])),
            "blocked_connection_timeout": int(
                os.getenv("RABBITMQ_TIMEOUT", self.DEFAULT_PARAMS["blocked_connection_timeout"])
            ),
        }

        user = os.getenv("RABBITMQ_DEFAULT_USER") or os.getenv("RABBITMQ_USER") or "guest"
        password = os.getenv("RABBITMQ_DEFAULT_PASS") or os.getenv("RABBITMQ_PASS") or "guest"

        if user and password:
            params["credentials"] = pika.PlainCredentials(user, password)

        return params