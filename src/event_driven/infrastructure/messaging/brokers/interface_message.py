import abc
from typing import Any


class IMessageBroker(abc.ABC):
    """Interfaz abstracta para cualquier broker de mensajes."""

    @abc.abstractmethod
    def publish(
        self,
        topic_or_queue: str,
        message: dict,
        exchange: str = "",
        routing_key: str | None = None,
    ) -> None:
        pass

    @abc.abstractmethod
    def consume(
        self,
        source: str,
        timeout: float = 1.0,
        exchange: str | None = None,
        routing_key: str | None = None,
    ) -> Any | None:
        pass
