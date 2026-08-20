import abc
from typing import Any, Optional


class IMessageBroker(abc.ABC):
    """Interfaz abstracta para cualquier broker de mensajes."""

    @abc.abstractmethod
    def publish(
        self,
        topic_or_queue: str,
        message: dict,
        exchange: str = "",
        routing_key: Optional[str] = None,
    ) -> None:
        pass

    @abc.abstractmethod
    def consume(
        self,
        source: str,
        timeout: float = 1.0,
        exchange: Optional[str] = None,
        routing_key: Optional[str] = None,
    ) -> Optional[Any]:
        pass