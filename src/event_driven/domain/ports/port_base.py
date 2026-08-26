import abc
from typing import Generic, Optional, TypeVar
from pydantic import BaseModel

# TypeVar constrained to Pydantic models or None
PayloadT = TypeVar("PayloadT", bound=BaseModel | None)


class BasePort(abc.ABC, Generic[PayloadT]):
    """Generic base interface for all repository ports in the Domain layer."""

    @abc.abstractmethod
    def save(self, entity: PayloadT) -> None:
        """Persists an entity or schema in the storage system."""
        raise NotImplementedError

    @abc.abstractmethod
    def get_by_id(self, entity_id: str) -> Optional[PayloadT]:
        """Retrieves an entity or schema by its unique identifier."""
        raise NotImplementedError

    @abc.abstractmethod
    def delete(self, entity_id: str) -> None:
        """Deletes an entity or schema by its unique identifier."""
        raise NotImplementedError