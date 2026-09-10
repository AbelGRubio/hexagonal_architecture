"""In-memory broker adapter implementation.

This module contains a local queue-based implementation used for development and
in-process messaging without requiring an external broker service.
"""

import queue
from collections.abc import Generator
from typing import Any

import orjson

from .interface_message import IMessageBroker


class LocalQueueAdapter(IMessageBroker):
    """Thread-safe in-memory queue adapter for local message processing.

    This adapter stores one queue per topic or queue name and provides the same
    publish/consume interface expected by the messaging abstraction.
    """

    def __init__(self) -> None:
        """Initialize the internal registry of named queues."""
        self.queues: dict[str, queue.Queue[Any]] = {}

    def _get_or_create_queue(self, name: str) -> queue.Queue[Any]:
        """Return an existing queue for the given name or create it if missing."""
        if name not in self.queues:
            self.queues[name] = queue.Queue()
        return self.queues[name]

    def publish(
        self,
        topic_or_queue: str,
        message: dict[str, Any],
        exchange_or_group: str = "",
    ) -> None:
        """Publish a message to the in-memory queue associated with a topic.

        Args:
            topic_or_queue: Name of the queue or logical topic.
            message: Message payload to serialize and enqueue.
            exchange_or_group: Unused in the local implementation but kept for
                interface compatibility.
        """
        q = self._get_or_create_queue(topic_or_queue)
        q.put(orjson.dumps(message).decode("utf-8"))

    def consume(
        self,
        topic_or_queue: str,
        exchange_or_group: str | None = None,
        timeout: float = 1.0,
    ) -> Generator[Any]:
        """Consume messages from the queue in a blocking, generator-based pattern.

        Args:
            topic_or_queue: Name of the queue to consume from.
            exchange_or_group: Unused in this implementation; kept for interface
                compatibility with other adapters.
            timeout: Idle timeout retained for parity with the shared interface,
                although the local queue implementation blocks until a message is
                available.

        Yields:
            The next serialized message payload as it becomes available.
        """
        q = self._get_or_create_queue(topic_or_queue)
        while True:
            msg = q.get(block=True)
            yield msg
