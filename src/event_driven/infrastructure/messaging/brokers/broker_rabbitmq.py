class RabbitMQAdapter(IMessageBroker):
    """Adaptador para RabbitMQ (usando pika)."""

    def __init__(self, host: str = "localhost"):
        import pika
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host=host))
        self.channel = self.connection.channel()

    def send(self, destination: str, message: dict) -> None:
        self.channel.queue_declare(queue=destination, durable=True)
        self.channel.basic_publish(
            exchange='',
            routing_key=destination,
            body=json.dumps(message)
        )

    def consume(self, source: str) -> Optional[Any]:
        self.channel.queue_declare(queue=source, durable=True)
        # Nota: RabbitMQ en un hilo suele requerir callbacks,
        # pero para adaptarlo al bucle 'get' puedes usar basic_get:
        method_frame, header_frame, body = self.channel.basic_get(queue=source, auto_ack=False)
        if method_frame:
            # Guardamos el delivery_tag para hacer el ACK más tarde si es necesario
            return {"body": body, "delivery_tag": method_frame.delivery_tag}
        return None

    def ack(self, delivery_tag: int):
        self.channel.basic_ack(delivery_tag=delivery_tag)