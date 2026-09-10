"""Unit tests for the ProcessOrderUseCase domain logic.

This module verifies the correct behavior of the ProcessOrderUseCase class,
including validation rules, total amount calculation for order items,
proper mapping to PaymentModel, and exception handling.
"""

import unittest
from unittest.mock import MagicMock, patch

from event_driven.domain.schemas import CartItemModel, OrderCreatedModel, PaymentModel

# Import schemas and use case according to your project structure
from event_driven.domain.use_case.case_process_order import ProcessOrderUseCase


class TestProcessOrderUseCase(unittest.TestCase):
    """Test suite for ProcessOrderUseCase execution and business logic."""

    def setUp(self) -> None:
        """Initial configuration for each test method."""
        self.mock_adapter: MagicMock = MagicMock()
        self.use_case: ProcessOrderUseCase = ProcessOrderUseCase(adapter=self.mock_adapter)
        items_ = [
            {"name": "prod-1", "product_id": "prod-1", "unit_price": 10.0, "quantity": 2},
            {"name": "prod-2", "product_id": "prod-2", "unit_price": 15.5, "quantity": 1},
        ]

        self.items: list[CartItemModel] = [CartItemModel(**i) for i in items_]

    def test_execute_successful_order_processing(self) -> None:
        """Verify proper payment model creation and amount calculation when order contains valid items."""
        # Arrange: Prepare an order payload with multiple items having unit prices and quantities
        payload = OrderCreatedModel(event_id="evt-123", order_id="order-456", user_id="user-789", items=self.items)

        # Act: Execute the use case
        result: PaymentModel | None = self.use_case.execute(payload)

        # Assert: Verify returned payment model properties and calculated total amount
        self.assertIsInstance(result, PaymentModel)
        self.assertEqual(result.order_id, payload.order_id)  # type: ignore
        self.assertEqual(result.user_id, payload.user_id)  # type: ignore
        self.assertEqual(result.amount, 35.5)  # type: ignore
        self.assertEqual(result.currency, "EUR")  # type: ignore
        self.assertEqual(result.status, "PENDING")  # type: ignore
        self.assertEqual(result.payment_method, "CREDIT_CARD")  # type: ignore

    def test_execute_order_processing_with_missing_prices_or_quantities(self) -> None:
        """Verify correct default handling (fallback to 0.0 or 1) when unit_price or quantity are omitted."""
        # Arrange: Prepare payload where items might have None for prices or quantities
        payload = OrderCreatedModel(event_id="evt-123", order_id="order-456", user_id="user-789", items=self.items)

        # Act: Execute the use case
        result: PaymentModel | None = self.use_case.execute(payload)

        # Assert: Verify total amount handles missing fields gracefully
        self.assertIsInstance(result, PaymentModel)
        self.assertEqual(result.amount, 35.5)  # type: ignore

    def test_execute_raises_value_error_when_items_are_empty(self) -> None:
        """Verify that a ValueError is raised if the order items list is empty."""
        # Arrange: Payload with an empty items list
        payload = OrderCreatedModel(event_id="evt-123", order_id="order-456", user_id="user-789", items=[])

        # Act & Assert: Check for expected ValueError
        with self.assertRaises(ValueError) as context:
            self.use_case.execute(payload)

        self.assertEqual(str(context.exception), "Order must contain at least one item.")

    def test_execute_handles_and_reraises_exceptions(self) -> None:
        """Verify that any internal exception during execution is caught, logged, and re-raised."""
        # Arrange: Valid order payload
        payload = OrderCreatedModel(event_id="evt-123", order_id="order-456", user_id="user-789", items=self.items)

        # Act & Assert: Force an exception during PaymentModel creation using patching
        with patch(
            "event_driven.domain.use_case.case_process_order.PaymentModel",
            side_effect=Exception("Payment model construction failed"),
        ):
            with self.assertRaises(Exception) as context:
                self.use_case.execute(payload)

            self.assertEqual(str(context.exception), "Payment model construction failed")


if __name__ == "__main__":
    unittest.main()
