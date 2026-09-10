"""RabbitMQ broker adapter implementation.

This module provides a concrete adapter for RabbitMQ using the pika client
with resilience patterns using tenacity.
"""

import logging
import os
from collections.abc import Generator
from typing import Any

import orjson
import pika
import pika.exceptions
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from event_driven.infrastructure.config.init_pybreaker import broker_pybreaker
from .interface_message import IMessageBroker

logger = logging.getLogger(__name__)


class RabbitMQAdapter(IMessageBroker):
    """RabbitMQ adapter implementation using pika with resilience."""

    DEFAULT_PARAMS = {
        "host": "localhost",
        "port": 5672,
        "heartbeat": 600,
        "blocked_connection_timeout": 300,
    }

    def __init__(self, **kwargs: Any) -> None:
        """Create a blocking RabbitMQ connection and open its channel with retries."""
        connection_params = self._get_default_params()

        if "username" in kwargs and "password" in kwargs:
            kwargs["credentials"] = pika.PlainCredentials(kwargs.pop("username"), kwargs.pop("password"))

        connection_params |= kwargs
        self.connection_params = connection_params
        self._connect()

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((pika.exceptions.AMQPConnectionError, ConnectionError, TimeoutError)),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )
    def _connect(self) -> None:
        """Establish connection and channel with retry logic if RabbitMQ is down on startup."""
        logger.info("Attempting to connect to RabbitMQ...")
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(**self.connection_params))
        self.channel = self.connection.channel()
        logger.info("Successfully connected to RabbitMQ.")

    @broker_pybreaker()
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=5),
        retry=retry_if_exception_type((
            pika.exceptions.AMQPChannelError,
            pika.exceptions.AMQPConnectionError,
            pika.exceptions.ConnectionClosed,
            pika.exceptions.ChannelClosed,
            pika.exceptions.ChannelWrongStateError,
            ConnectionError,
            TimeoutError,
        )),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )
    def publish(
        self,
        topic_or_queue: str,
        message: dict[str, Any],
        exchange_or_group: str = "",
    ) -> None:
        """Publish a message to a RabbitMQ queue or exchange with automatic retries."""
        if not self.connection or self.connection.is_closed or not self.channel or self.channel.is_closed:
            logger.warning("RabbitMQ connection or channel found closed during publish. Reconnecting...")
            self._connect()

        rk = topic_or_queue

        # If publishing to the default exchange, declare the queue.
        if exchange_or_group == "":
            self.channel.queue_declare(queue=topic_or_queue, durable=True)
        else:
            self.channel.exchange_declare(exchange=exchange_or_group, exchange_type="direct", durable=True)

        self.channel.basic_publish(
            exchange=exchange_or_group,
            routing_key=rk,
            body=orjson.dumps(message),
            properties=pika.BasicProperties(delivery_mode=2),
        )

    @broker_pybreaker()
    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        retry=retry_if_exception_type((
            pika.exceptions.AMQPConnectionError,
            pika.exceptions.StreamLostError,
            pika.exceptions.ConnectionClosed,
            pika.exceptions.ChannelClosed,
            pika.exceptions.ChannelWrongStateError,
            ConnectionError,
            TimeoutError,
        )),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )
    def consume(
        self,
        topic_or_queue: str,
        exchange_or_group: str | None = None,
        timeout: float = 1.0,
    ) -> Generator[Any]:
        """Consume messages from a RabbitMQ queue.

        Note: Consuming loops are usually continuous generators where reconnection
        is handled at the worker or higher level, but timeouts are managed via inactivity_timeout.
        """
        if not self.connection or self.connection.is_closed or not self.channel or self.channel.is_closed:
            logger.warning("RabbitMQ connection or channel found closed before consume. Reconnecting...")
            self._connect()

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
        except (
            pika.exceptions.AMQPConnectionError,
            pika.exceptions.StreamLostError,
            pika.exceptions.ConnectionClosed,
            pika.exceptions.ChannelClosed,
            pika.exceptions.ChannelWrongStateError,
            ConnectionError,
        ) as exc:
            logger.error(f"Connection lost during consumption from {topic_or_queue}: {exc}")
            raise
        finally:
            try:
                self.channel.cancel()
            except Exception:
                pass

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
