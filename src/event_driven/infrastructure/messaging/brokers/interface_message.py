"""Abstract messaging broker contract.

This module defines the common interface shared by all broker adapters used in
this project, regardless of the underlying technology.
"""

import abc
from collections.abc import Generator
from typing import Any


class IMessageBroker(abc.ABC):
    """Abstract interface for any message broker implementation."""

    @abc.abstractmethod
    def publish(
        self,
        topic_or_queue: str,
        message: dict[str, Any],
        exchange_or_group: str = "",
    ) -> None:
        """Publish a message to the target topic or queue.

        Args:
            topic_or_queue: Destination topic or queue name.
            message: Message payload to send.
            exchange_or_group: Optional exchange or consumer group identifier,
                depending on the broker implementation.
        """
        pass

    @abc.abstractmethod
    def consume(
        self,
        topic_or_queue: str,
        exchange_or_group: str | None = None,
        timeout: float = 1.0,
    ) -> Generator[Any]:
        """Consume messages from the target topic or queue.

        Args:
            topic_or_queue: Source topic or queue name.
            exchange_or_group: Optional exchange or group name used by the broker.
            timeout: Maximum wait time before the broker returns no message.

        Yields:
            The next consumed message payload.
        """
        pass
