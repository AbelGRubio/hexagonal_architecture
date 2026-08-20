import abc
from typing import Any, Optional


class IMessageBroker(abc.ABC):
    """Interfaz abstracta para cualquier broker de mensajes."""

    @abc.abstractmethod
    def publish(self, topic_or_queue: str, message: dict) -> None:
        pass

    @abc.abstractmethod
    def consume(self, source: str, timeout: float = 1.0) -> Optional[Any]:
        pass