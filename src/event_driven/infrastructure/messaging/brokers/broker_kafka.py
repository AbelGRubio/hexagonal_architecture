"""Kafka broker adapter implementation.

This module exposes the Kafka-specific adapter used to publish and consume
messages through the shared messaging interface.
"""

from typing import Any

import orjson
from confluent_kafka import Message, Consumer, Producer

from event_driven.logger import get_logger

from .interface_message import IMessageBroker

logger = get_logger(__name__)


class KafkaAdapter(IMessageBroker):
    """Adapter for Apache Kafka using the confluent-kafka client."""

    DEFAULT_PRODUCER_CONFIG: dict[str, Any] = {
        "bootstrap.servers": "localhost:9092",
        "acks": "all",
        "retries": 3,
        "compression.type": "snappy",
        "queue.buffering.max.messages": 100000,
    }

    def __init__(self, **kwargs: Any) -> None:
        """Create the Kafka producer and initialize the pool of topic consumers."""

        final_config = self.DEFAULT_PRODUCER_CONFIG.copy()
        if kwargs:
            final_config.update(kwargs)

        self.bootstrap_servers: str = final_config["bootstrap.servers"]

        # Producer configuration
        self.producer_config: dict[str, Any] = final_config
        self.producer: Producer = Producer(self.producer_config)

        # Keep active consumers by topic
        self.consumers: dict[str, Consumer] = {}

    def _get_or_create_consumer(self, topic: str, exchange_or_group: str | None = '') -> Consumer:
        """Return a cached Kafka consumer for the given topic, creating it on demand."""
        if topic not in self.consumers:
            conf: dict[str, Any] = {
                "bootstrap.servers": self.bootstrap_servers,
                "group.id": exchange_or_group or 'kafka-group-infra',
                "auto.offset.reset": "earliest",
                "enable.auto.commit": False,
            }
            consumer = Consumer(conf)
            consumer.subscribe([topic])
            self.consumers[topic] = consumer
        return self.consumers[topic]

    def publish(
        self,
        topic_or_queue: str,
        message: dict[str, Any],
        exchange_or_group: str = "",
    ) -> None:
        """Publish a message to a Kafka topic.

        The `exchange` and `routing_key` arguments are ignored because Kafka does not
        use those concepts in the same way as AMQP brokers.
        """

        def delivery_report(err: Any, msg: Message | None) -> None:
            if err is not None:
                logger.error(f"[Kafka] Error sending message: {err}")
                return

            if msg is not None:
                logger.info(f"[Kafka] Message sent to {msg.topic()} [{msg.partition()}]")

        self.producer.produce(
            topic=topic_or_queue,
            value=orjson.dumps(message),
            callback=delivery_report,
        )
        self.producer.poll(0)
        self.producer.flush()

    def consume(
        self,
        topic_or_queue: str,
        exchange_or_group: str | None = None,
        timeout: float = 1.0,
    ) -> tuple[Any | None, None]:
        """Consume a single message from a Kafka topic.

        Args:
            topic_or_queue: Target topic name.
            exchange_or_group: Consumer group identifier used by Kafka.
            timeout: Maximum time to wait for a message in seconds.

        Returns:
            A tuple containing the deserialized payload and a second value set to
            `None` for compatibility with the broker interface.
        """
        consumer = self._get_or_create_consumer(topic_or_queue, exchange_or_group=exchange_or_group)

        msg = consumer.poll(timeout=timeout)

        if msg is None:
            return None, None
        if msg.error():
            logger.error(f"[Kafka] Error while consuming: {msg.error()}")
            return None, None

        return orjson.loads(msg.value()), None

    def commit(self, consumer: Consumer, raw_msg: Message) -> None:
        """Commit a Kafka message to acknowledge successful processing."""
        consumer.commit(message=raw_msg, asynchronous=False)
