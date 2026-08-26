from typing import Type

from typing import Type

from event_driven.infrastructure.config.enumerations import ThreadsEnum
from event_driven.infrastructure.threads.thread_base import BaseWorkerThread
from event_driven.infrastructure.threads.thread_inventory import InventoryThread
from event_driven.infrastructure.threads.thread_notification import NotificationThread
from event_driven.infrastructure.threads.thread_order import OrderThread
from event_driven.infrastructure.threads.thread_payment import PaymentThread

# ------------------------------------------------------------------
# REGISTRIES & ENUMS (Easily extensible to add more workers/brokers)
# ------------------------------------------------------------------


THREAD_REGISTRY: dict[ThreadsEnum, Type[BaseWorkerThread]] = {
    ThreadsEnum.INVENTORY: InventoryThread,
    ThreadsEnum.NOTIFICATION: NotificationThread,
    ThreadsEnum.ORDER: OrderThread,
    ThreadsEnum.PAYMENT: PaymentThread,
}
