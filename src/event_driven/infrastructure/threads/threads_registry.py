from typing import Type

from event_driven.infrastructure.config.enumerations import ThreadsEnum
from event_driven.infrastructure.threads import BaseWorkerThread, InventoryThread, NotificationThread, OrderThread, \
    PaymentThread

# ------------------------------------------------------------------
# REGISTRIES & ENUMS (Easily extensible to add more workers/brokers)
# ------------------------------------------------------------------


THREAD_REGISTRY: dict[ThreadsEnum, Type[BaseWorkerThread]] = {
    ThreadsEnum.INVENTORY: InventoryThread,
    ThreadsEnum.NOTIFICATION: NotificationThread,
    ThreadsEnum.ORDER: OrderThread,
    ThreadsEnum.PAYMENT: PaymentThread,
}
