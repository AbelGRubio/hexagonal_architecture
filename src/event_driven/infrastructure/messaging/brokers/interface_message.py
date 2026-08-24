import abc
from typing import Any, Generator


class IMessageBroker(abc.ABC):
    """Interfaz abstracta para cualquier broker de mensajes."""

    @abc.abstractmethod
    def publish(
        self,
        topic_or_queue: str,
        message: dict,
        exchange_or_group: str = "",
    ) -> None:
        pass

    @abc.abstractmethod
    def consume(
        self,
        topic_or_queue: str,
        exchange_or_group: str = '',
        timeout: float = 1.0,
    ) -> Generator[Any, None, None]:
        pass
