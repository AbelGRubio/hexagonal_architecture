"""Unit tests for the PaymentUseCase domain logic.

This module verifies the correct behavior of the PaymentUseCase class,
including validation rules, branching logic for successful or failed payments,
proper mapping to NotificationModel, and exception handling.
"""

import unittest
from unittest.mock import MagicMock, patch

from event_driven.domain.schemas import NotificationModel, PaymentModel

# Import schemas and use case according to your project structure
from event_driven.domain.use_case.case_payment import PaymentUseCase


class TestPaymentUseCase(unittest.TestCase):
    """Test suite for PaymentUseCase execution and business logic."""

    def setUp(self) -> None:
        """Initial configuration for each test method."""
        self.mock_adapter: MagicMock = MagicMock()

    def test_execute_successful_payment(self) -> None:
        """Verify proper notification creation when payment status is SUCCESS."""
        # Arrange: Initialize use case and create a successful payment payload
        use_case = PaymentUseCase(adapter=self.mock_adapter)
        payload = PaymentModel(
            payment_id="pay-123",
            order_id="order-456",
            user_id="user-789",
            amount=100.50,
            currency="USD",
            status="SUCCESS",
        )

        # Act: Execute the use case
        result: NotificationModel | None = use_case.execute(payload)

        # Assert: Verify returned notification properties for a successful payment
        self.assertIsInstance(result, NotificationModel)
        self.assertEqual(result.order_id, payload.order_id)  # type: ignore
        self.assertEqual(result.user_id, payload.user_id)  # type: ignore
        self.assertEqual(result.status, "PENDING")  # type: ignore
        self.assertIn("Confirmed!", result.subject)  # type: ignore
        self.assertIn("100.5", result.message)  # type: ignore
        self.assertEqual(result.recipient, "user_user-789@example.com")  # type: ignore

    def test_execute_failed_payment(self) -> None:
        """Verify proper notification creation when payment status is not SUCCESS (failed)."""
        # Arrange: Initialize use case and create a failed payment payload
        use_case = PaymentUseCase(adapter=self.mock_adapter)
        payload = PaymentModel(
            payment_id="pay-123",
            order_id="order-456",
            user_id="",  # Test fallback recipient when user_id is empty
            amount=50.00,
            currency="EUR",
            status="FAILED",
        )

        # Act: Execute the use case
        result: NotificationModel | None = use_case.execute(payload)

        # Assert: Verify returned notification properties for a failed payment
        self.assertIsInstance(result, NotificationModel)
        self.assertEqual(result.status, "FAILED")  # type: ignore
        self.assertIn("Payment Failed", result.subject)  # type: ignore
        self.assertIn("issue processing", result.message)  # type: ignore
        self.assertEqual(result.recipient, "customer@example.com")  # type: ignore

    def test_execute_raises_value_error_when_amount_is_zero_or_negative(self) -> None:
        """Verify that a ValueError is raised if the payment amount is zero or negative."""
        # Arrange: Payload with invalid amount
        use_case = PaymentUseCase(adapter=self.mock_adapter)
        payload = PaymentModel(
            payment_id="pay-123",
            order_id="order-456",
            user_id="user-789",
            amount=0.00,
            currency="USD",
            status="SUCCESS",
        )

        # Act & Assert: Check for expected ValueError
        with self.assertRaises(ValueError) as context:
            use_case.execute(payload)

        self.assertEqual(str(context.exception), "Payment amount must be greater than zero.")

    def test_execute_handles_and_reraises_exceptions(self) -> None:
        """Verify that any internal exception is caught, logged, and re-raised."""
        # Arrange: Initialize use case and payload
        use_case = PaymentUseCase(adapter=self.mock_adapter)
        payload = PaymentModel(
            payment_id="pay-123",
            order_id="order-456",
            user_id="user-789",
            amount=75.00,
            currency="USD",
            status="SUCCESS",
        )

        # Act & Assert: Force an exception during NotificationModel creation using patching
        with patch(
            "event_driven.domain.use_case.case_payment.NotificationModel",
            side_effect=Exception("Model generation failure"),
        ):
            with self.assertRaises(Exception) as context:
                use_case.execute(payload)

            self.assertEqual(str(context.exception), "Model generation failure")


if __name__ == "__main__":
    unittest.main()
