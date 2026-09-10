"""Kafka broker adapter implementation.

This module exposes the Kafka-specific adapter used to publish and consume
messages through the shared messaging interface, integrated with tenacity resilience.
"""

import logging
from typing import Any

import orjson
from confluent_kafka import Consumer, KafkaException, Message, Producer
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from event_driven.logger import get_logger

from .interface_message import IMessageBroker

logger = get_logger(__name__)


class KafkaAdapter(IMessageBroker):
    """Adapter for Apache Kafka using the confluent-kafka client with resilience."""

    DEFAULT_PRODUCER_CONFIG: dict[str, Any] = {
        "bootstrap.servers": "localhost:9092",
        "acks": "all",
        "retries": 3,
        "compression.type": "snappy",
        "queue.buffering.max.messages": 100000,
    }

    def __init__(self, **kwargs: Any) -> None:
        """Create the Kafka producer and initialize connection configuration."""
        final_config = self.DEFAULT_PRODUCER_CONFIG | kwargs
        self.bootstrap_servers: str = final_config["bootstrap.servers"]
        self.producer_config: dict[str, Any] = final_config

        # Inicializar productor con reintentos
        self.producer: Producer = self._create_producer(self.producer_config)
        self.consumers: dict[str, Consumer] = {}

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((KafkaException, ConnectionError, TimeoutError)),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )
    def _create_producer(self, config: dict[str, Any]) -> Producer:
        """Create Kafka Producer with retry logic on startup/connection failure."""
        logger.info("Initializing Kafka Producer...")
        return Producer(config)

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((KafkaException, ConnectionError, TimeoutError)),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )
    def _get_or_create_consumer(self, topic: str, exchange_or_group: str | None = "") -> Consumer:
        """Return a cached Kafka consumer for the given topic, with automatic retry on failure."""
        if topic not in self.consumers:
            logger.info(f"Creating Kafka consumer for topic '{topic}'...")
            conf: dict[str, Any] = {
                "bootstrap.servers": self.bootstrap_servers,
                "group.id": exchange_or_group or "kafka-group-infra",
                "auto.offset.reset": "earliest",
                "enable.auto.commit": False,
            }
            consumer = Consumer(conf)
            consumer.subscribe([topic])
            self.consumers[topic] = consumer
        return self.consumers[topic]

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=5),
        retry=retry_if_exception_type((KafkaException, ConnectionError, TimeoutError)),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )
    def publish(
        self,
        topic_or_queue: str,
        message: dict[str, Any],
        exchange_or_group: str = "",
    ) -> None:
        """Publish a message to a Kafka topic with automatic retries."""

        def delivery_report(err: Any, msg: Message | None) -> None:
            if err is not None:
                logger.error(f"[Kafka] Error sending message: {err}")
                raise KafkaException(err)

            if msg is not None:
                logger.info(f"[Kafka] Message sent to {msg.topic()} [{msg.partition()}]")

        self.producer.produce(
            topic=topic_or_queue,
            value=orjson.dumps(message),
            callback=delivery_report,
        )
        self.producer.poll(0)

        # El flush lanza excepciones si falla el envío final tras los reintentos internos
        self.producer.flush()

    def consume(
        self,
        topic_or_queue: str,
        exchange_or_group: str | None = None,
        timeout: float = 1.0,
    ) -> tuple[Any | None, None]:
        """Consume a single message from a Kafka topic with recovery on network errors."""
        try:
            consumer = self._get_or_create_consumer(topic_or_queue, exchange_or_group=exchange_or_group)
            msg = consumer.poll(timeout=timeout)

            if msg is None:
                return None, None

            if msg.error():
                err = msg.error()
                logger.error(f"[Kafka] Error while consuming: {err}")
                # Si es un error crítico del broker, lanzamos excepción para forzar el retry
                if err.fatal() or err.is_retriable():
                    raise KafkaException(err)
                return None, None

            return orjson.loads(msg.value()), None

        except (KafkaException, ConnectionError) as exc:
            logger.error(f"[Kafka] Connection error during consumption on {topic_or_queue}: {exc}")
            raise  # Esto activa Tenacity

    def commit(self, consumer: Consumer, raw_msg: Message) -> None:
        """Commit a Kafka message to acknowledge successful processing."""
        consumer.commit(message=raw_msg, asynchronous=False)
