class LocalQueueAdapter(IMessageBroker):
    """Adaptador para usar colas en memoria de Python (threading-safe)."""

    def __init__(self):
        self.queues: dict[str, queue.Queue] = {}

    def _get_or_create_queue(self, name: str) -> queue.Queue:
        if name not in self.queues:
            self.queues[name] = queue.Queue()
        return self.queues[name]

    def send(self, destination: str, message: dict) -> None:
        q = self._get_or_create_queue(destination)
        q.put(json.dumps(message))

    def consume(self, source: str) -> Optional[Any]:
        q = self._get_or_create_queue(source)
        try:
            # Timeout de 1 segundo para permitir que los hilos cierren limpiamente
            return q.get(timeout=1.0)
        except queue.Empty:
            return None