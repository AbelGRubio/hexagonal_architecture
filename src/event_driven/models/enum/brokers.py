from enum import Enum

class Broker(Enum):
    KAFKA = 'kafka'
    LOCAL = 'local'
    RABBITMQ = 'rabbitmq'
