"""Cart items producer thread implementation."""

import logging
import random
import time
import uuid
from typing import Final

from event_driven.domain.schemas import CartItemModel, CartItemsModel
from event_driven.infrastructure.config.schemas import ThreadConfigModel

from .thread_base import BaseWorkerThread

logger = logging.getLogger(__name__)

# Predefined base product catalog names
PRODUCT_BASE_NAMES: Final[list[str]] = [
    "Laptop Pro 15",
    "Wireless Mouse",
    "Mechanical Keyboard",
    'USB-C Monitor 27"',
]


class ProducerThread(BaseWorkerThread[CartItemsModel, CartItemsModel]):
    """Worker thread that generates deterministic, synthetic CartItems messages and sends them to RabbitMQ."""

    DEFAULT_QUEUE = "cart-items"

    def __init__(
        self,
        config: ThreadConfigModel,
        interval_seconds: float = 2.0,
        seed: int = 42,
    ) -> None:
        """Initialize the cart items producer thread.

        Args:
            config: Brokers configurations
            interval_seconds: Delay in seconds between generated messages.
            seed: Seed value for reproducible random sequence generation.
        """
        super().__init__(payload_model=CartItemsModel, config=config)
        self.counter = 0
        self.interval_seconds: float = interval_seconds
        self._rng: random.Random = random.Random(seed)
        self._counter: int = 0
        self._is_running: bool = False

    def process_payload(self, payload: CartItemsModel) -> None:
        return None

    def run(self) -> None:
        """Main execution loop that generates and publishes payload items continuously."""
        self._init_brokers()
        queue_ = self.config.producer.topic_or_queue or ""
        logger.info(f"Producer thread started. Target topic: '{queue_}'.")
        self._is_running = True

        while self._is_running and self.producer_broker:
            try:
                payload: CartItemsModel = self._generate_cart_items()

                self.producer_broker.publish(
                    topic_or_queue=queue_,
                    message=payload.model_dump(by_alias=True),
                )
                logger.info(
                    f"Successfully published {len(payload.items)} item(s) to '{queue_}'. "
                    f"Nº Chart generated: {self.counter}. CartID: {payload.id}."
                )
                self.counter += 1
            except Exception as exc:
                logger.error(f"Error occurred while publishing message: {exc}", exc_info=True)

            time.sleep(self.interval_seconds)

    def _generate_cart_items(self) -> CartItemsModel:
        """Generate a CartItemsModel containing a random batch of items.

        Returns:
            CartItemsModel: Payload wrapper holding generated cart items.
        """
        item_count: int = self._rng.randint(1, 4)
        items: list[CartItemModel] = [self._generate_cart_item() for _ in range(item_count)]
        unique_id: str = str(uuid.UUID(int=self._rng.getrandbits(128), version=4))
        return CartItemsModel(items=items, id=unique_id)

    def _generate_cart_item(self) -> CartItemModel:
        """Generate a single random CartItemModel with structured fields.

        Returns:
            CartItemModel: Populated Pydantic cart item instance.
        """
        self._counter += 1

        # Product ID strictly following "prod-<integer>"
        product_id: str = f"prod-{self._rng.randint(100, 999)}"

        # Select a base name and append non-repeating sequence number
        base_name: str = self._rng.choice(PRODUCT_BASE_NAMES)
        item_name: str = f"{base_name} #{self._counter}"

        # Unit price formatted as float rounded to 2 decimal places
        unit_price: float = round(self._rng.uniform(5.00, 1500.00), 2)
        quantity: int = self._rng.randint(1, 5)

        return CartItemModel(
            product_id=product_id,
            name=item_name,
            unit_price=unit_price,
            quantity=quantity,
        )
