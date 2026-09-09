import unittest
from unittest.mock import MagicMock
from datetime import datetime
from typing import Optional

# Import schemas and use case according to your project structure
from event_driven.domain.use_case.case_check_inventory import CheckInventoryUseCase
from event_driven.domain.schemas import CartItemsModel, OrderCreatedModel


class TestCheckInventoryUseCase(unittest.TestCase):

    def setUp(self) -> None:
        """Initial configuration for each test method."""
        self.mock_adapter: MagicMock = MagicMock()
        self.use_case: CheckInventoryUseCase = CheckInventoryUseCase(adapter=self.mock_adapter)

    def test_execute_successful_order_creation(self) -> None:
        """Verify that the order is successfully created when the cart contains valid items."""
        # Arrange: Prepare a payload with valid items
        payload = CartItemsModel(
            id="event-uuid-123",
            items=[{"product_id": "prod-1", "quantity": 2}]
        )

        # Act: Execute the use case
        result: Optional[OrderCreatedModel] = self.use_case.execute(payload)

        # Assert: Verify that it returns an OrderCreatedModel instance with correct data
        self.assertIsInstance(result, OrderCreatedModel)
        self.assertEqual(result.event_id, payload.id)  # type: ignore
        self.assertEqual(result.items, payload.items)  # type: ignore
        self.assertIsNotNone(result.order_id)  # type: ignore
        self.assertIsNotNone(result.user_id)  # type: ignore
        self.assertIsInstance(result.timestamp, datetime)  # type: ignore

    def test_execute_raises_value_error_when_items_are_empty(self) -> None:
        """Verify that a ValueError is raised if the cart does not contain any items."""
        # Arrange: Payload with an empty items list
        payload = CartItemsModel(
            id="event-uuid-123",
            items=[]
        )

        # Act & Assert: Check that the expected ValueError is raised
        with self.assertRaises(ValueError) as context:
            self.use_case.execute(payload)

        self.assertEqual(str(context.exception), "Order must contain at least one item.")

    def test_execute_handles_exception_gracefully(self) -> None:
        """Verify that if an internal exception occurs, it is caught and returns None."""
        # Arrange: Create a valid payload
        payload = CartItemsModel(
            id="event-uuid-123",
            items=[{"product_id": "prod-1", "quantity": 1}]
        )

        # Act: Simulate an internal error within the try block using patching
        with unittest.mock.patch(
                "event_driven.domain.use_case.case_check_inventory.OrderCreatedModel",
                side_effect=Exception("Database or internal error")
        ):
            result: Optional[OrderCreatedModel] = self.use_case.execute(payload)

        # Assert: Must catch the exception, log it, and return None
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()