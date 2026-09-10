"""Unit tests for the BasePort abstract interface.

This module verifies the correct behavior of the generic BasePort abstract class,
ensuring that it cannot be instantiated directly and that concrete implementations
satisfy the required interface contract.
"""

import unittest

from pydantic import BaseModel

# Import BasePort from the corresponding path
from event_driven.domain.ports.port_base import BasePort


class DummyModel(BaseModel):
    """Auxiliary Pydantic model for testing the generic PayloadT type."""

    id: str
    name: str


class DummyPort(BasePort[DummyModel]):
    """Concrete implementation of BasePort for testing purposes."""

    def __init__(self) -> None:
        self.storage: dict[str, DummyModel] = {}

    def save(self, entity: DummyModel) -> None:
        if entity:
            self.storage[entity.id] = entity

    def get_by_id(self, entity_id: str) -> DummyModel | None:
        return self.storage.get(entity_id)

    def delete(self, entity_id: str) -> None:
        if entity_id in self.storage:
            del self.storage[entity_id]


class TestBasePort(unittest.TestCase):
    """Test suite for BasePort abstract class behavior."""

    def test_cannot_instantiate_abstract_class(self) -> None:
        """Verify that BasePort cannot be instantiated directly as an abstract class."""
        with self.assertRaises(TypeError):
            BasePort()  # type: ignore

    def test_concrete_port_operations(self) -> None:
        """Verify the complete CRUD-like lifecycle (save, get_by_id, delete) in a concrete implementation."""
        port: DummyPort = DummyPort()
        entity: DummyModel = DummyModel(id="123", name="Test Entity")

        # Test save and get_by_id
        port.save(entity)
        retrieved: DummyModel | None = port.get_by_id("123")

        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved, entity)
        self.assertEqual(retrieved.name, "Test Entity")  # type: ignore

        # Test delete
        port.delete("123")
        deleted_entity: DummyModel | None = port.get_by_id("123")
        self.assertIsNone(deleted_entity)

    def test_get_non_existent_entity(self) -> None:
        """Verify that retrieving a non-existent ID returns None."""
        port: DummyPort = DummyPort()
        result: DummyModel | None = port.get_by_id("non-existent-id")
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
