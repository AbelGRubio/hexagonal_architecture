import abc
from typing import Any, Optional


# Opcional: imports reales si usaras librerías externas
# import pika
# from confluent_kafka import Producer, Consumer


class IMessageBroker(abc.ABC):
    """Interfaz abstracta para cualquier broker de mensajes."""

    @abc.abstractmethod
    def send(self, destination: str, message: dict) -> None:
        pass

    @abc.abstractmethod
    def consume(self, source: str) -> Optional[Any]:
        pass