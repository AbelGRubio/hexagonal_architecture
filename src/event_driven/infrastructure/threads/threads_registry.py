from event_driven.infrastructure.config.enumerations import ThreadsEnum
from event_driven.infrastructure.threads import (
    BaseWorkerThread,
    ErrorThread,
    InventoryThread,
    NotificationThread,
    OrderThread,
    PaymentThread,
    ProducerThread,
)

# ------------------------------------------------------------------
# REGISTRIES & ENUMS (Easily extensible to add more workers/brokers)
# ------------------------------------------------------------------


THREAD_REGISTRY: dict[ThreadsEnum, type[BaseWorkerThread]] = {
    ThreadsEnum.INVENTORY: InventoryThread,
    ThreadsEnum.NOTIFICATION: NotificationThread,
    ThreadsEnum.ORDER: OrderThread,
    ThreadsEnum.PAYMENT: PaymentThread,
    ThreadsEnum.PRODUCER: ProducerThread,
    ThreadsEnum.ERROR: ErrorThread,
}
