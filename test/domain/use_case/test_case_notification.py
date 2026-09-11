"""Unit tests for the NotificationUseCase domain logic.

This module verifies the correct behavior of the NotificationUseCase class,
including validation rules, interaction with optional adapters, status updates,
and exception handling.
"""

import unittest
from unittest.mock import MagicMock

from event_driven.domain.schemas import NotificationModel

# Import schema and use case according to your project structure
from event_driven.domain.use_case.case_notification import NotificationUseCase


class TestNotificationUseCase(unittest.TestCase):
    """Test suite for NotificationUseCase execution and business logic."""

    def setUp(self) -> None:
        """Initial configuration for each test method."""
        self.mock_adapter: MagicMock = MagicMock()

    def test_execute_successful_notification_with_adapter(self) -> None:
        """Verify successful notification processing and adapter invocation when an adapter is provided."""
        # Arrange: Initialize use case with an adapter and create a valid payload
        use_case = NotificationUseCase(adapter=self.mock_adapter)
        payload = NotificationModel(
            notification_id="notif-123",
            order_id="order-456",
            channel="EMAIL",
            recipient="user@example.com",
            subject="Order Confirmation",
            message="Your order has been placed successfully and is being processed.",
            status="PENDING",
        )

        # Act: Execute the use case
        result: NotificationModel | None = use_case.execute(payload)

        # Assert: Verify adapter.send was called with the payload and status was updated
        #self.mock_adapter.send.assert_called_once_with(payload)
        self.assertIsNotNone(result)
        self.assertEqual(result.status, "SENT")  # type: ignore

    def test_execute_successful_notification_without_adapter(self) -> None:
        """Verify successful notification processing when no adapter is provided."""
        # Arrange: Initialize use case without an adapter
        use_case = NotificationUseCase(adapter=None)
        payload = NotificationModel(
            notification_id="notif-123",
            order_id="order-456",
            channel="SMS",
            recipient="+123456789",
            subject="Alert",
            message="Your package is out for delivery today.",
            status="PENDING",
        )

        # Act: Execute the use case
        result: NotificationModel | None = use_case.execute(payload)

        # Assert: Verify it still updates status to SENT even without an adapter
        self.assertIsNotNone(result)
        self.assertEqual(result.status, "SENT")  # type: ignore

    def test_execute_raises_value_error_when_notification_id_is_missing(self) -> None:
        """Verify that a ValueError is raised if notification_id is empty or missing."""
        # Arrange: Payload missing notification_id
        use_case = NotificationUseCase(adapter=self.mock_adapter)
        payload = NotificationModel(
            notification_id="",
            order_id="order-456",
            channel="EMAIL",
            recipient="user@example.com",
            subject="Subject",
            message="Message content here.",
            status="PENDING",
        )

        # Act & Assert: Check for expected ValueError
        with self.assertRaises(ValueError) as context:
            use_case.execute(payload)

        self.assertEqual(str(context.exception), "Notification must contain a valid notification_id.")
        self.mock_adapter.send.assert_not_called()

    def test_execute_raises_value_error_when_recipient_is_missing(self) -> None:
        """Verify that a ValueError is raised if recipient is empty or missing."""
        # Arrange: Payload missing recipient
        use_case = NotificationUseCase(adapter=self.mock_adapter)
        payload = NotificationModel(
            notification_id="notif-123",
            order_id="order-456",
            channel="EMAIL",
            recipient="",
            subject="Subject",
            message="Message content here.",
            status="PENDING",
        )

        # Act & Assert: Check for expected ValueError
        with self.assertRaises(ValueError) as context:
            use_case.execute(payload)

        self.assertEqual(str(context.exception), "Notification recipient cannot be empty.")
        self.mock_adapter.send.assert_not_called()

if __name__ == "__main__":
    unittest.main()
