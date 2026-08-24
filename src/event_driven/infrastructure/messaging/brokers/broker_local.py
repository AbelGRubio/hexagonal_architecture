import queue
from typing import Any, Generator

import orjson

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
        exchange_or_group: str = "",
    ) -> None:
        q = self._get_or_create_queue(topic_or_queue)
        q.put(orjson.dumps(message).decode("utf-8"))

    def consume(
        self,
        topic_or_queue: str,
        exchange_or_group: str | None = None,
        timeout: float = 1.0,
    ) -> Generator[Any, None, None]:
        q = self._get_or_create_queue(topic_or_queue)
        while True:
            msg = q.get(block=True)
            yield msg
