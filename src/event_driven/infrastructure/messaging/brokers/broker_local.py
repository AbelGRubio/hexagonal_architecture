import orjson
import queue
from typing import Any, Optional

from .interface_message import IMessageBroker


class LocalQueueAdapter(IMessageBroker):
    """Adaptador para usar colas en memoria de Python (threading-safe)."""

    def __init__(self):
        self.queues: dict[str, queue.Queue] = {}

    def _get_or_create_queue(self, name: str) -> queue.Queue:
        if name not in self.queues:
            self.queues[name] = queue.Queue()
        return self.queues[name]

    def publish(
        self,
        topic_or_queue: str,
        message: dict,
        exchange: str = "",
        routing_key: Optional[str] = None,
    ) -> None:
        q = self._get_or_create_queue(topic_or_queue)
        q.put(orjson.dumps(message).decode("utf-8"))

    def consume(
        self,
        source: str,
        timeout: float = 1.0,
        exchange: Optional[str] = None,
        routing_key: Optional[str] = None,
    ) -> Optional[Any]:
        q = self._get_or_create_queue(source)
        try:
            # Timeout de 1 segundo para permitir que los hilos cierren limpiamente
            return q.get(timeout=timeout)
        except queue.Empty:
            return None