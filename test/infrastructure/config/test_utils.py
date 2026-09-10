"""Unit tests for thread configuration resolver utilities.

This module validates field alias extraction, default broker resolution,
ThreadConfigModel inspection, and dictionary mutation logic for fallback settings.
"""

from enum import Enum
from typing import Any

from event_driven.infrastructure.config.utils import (
    BROKER_KWARGS,
    BROKER_TYPE,
    _apply_broker_defaults_to_section,
    _extract_defaults_by_type,
    _get_broker_section_names,
    _get_field_aliases,
)


class DummyBrokerEnum(Enum):
    """Dummy broker enum used for value extraction testing."""

    RABBITMQ = "rabbitmq"
    KAFKA = "kafka"


# ==========================================
# 1. Alias & Section Utility Tests
# ==========================================


def test_get_field_aliases_returns_valid_strings() -> None:
    """Verify _get_field_aliases returns proper tuple of strings for broker model fields."""
    kwargs_alias, type_alias, topic_alias = _get_field_aliases()

    assert isinstance(kwargs_alias, str)
    assert isinstance(type_alias, str)
    assert isinstance(topic_alias, str)
    assert len(kwargs_alias) > 0
    assert len(type_alias) > 0
    assert len(topic_alias) > 0


def test_get_broker_section_names_returns_list() -> None:
    """Verify _get_broker_section_names inspects ThreadConfigModel and returns field names."""
    sections = _get_broker_section_names()

    assert isinstance(sections, list)
    # ThreadConfigModel contains broker fields (e.g., consumer, producer, etc.)
    assert len(sections) > 0


# ==========================================
# 2. Extract Defaults Tests
# ==========================================


def test_extract_defaults_by_type_with_broker_config_key() -> None:
    """Verify _extract_defaults_by_type extracts global default and maps broker_config items."""
    raw_data: dict[str, Any] = {
        "default": "KAFKA",
        "broker_config": [
            {
                BROKER_TYPE: "kafka",
                BROKER_KWARGS: {"bootstrap_servers": "localhost:9092"},
            },
            {
                BROKER_TYPE: DummyBrokerEnum.RABBITMQ,
                BROKER_KWARGS: {"host": "localhost"},
            },
        ],
    }

    global_default, defaults_map = _extract_defaults_by_type(raw_data)

    assert global_default == "kafka"
    assert "kafka" in defaults_map
    assert "rabbitmq" in defaults_map
    assert defaults_map["kafka"][BROKER_KWARGS] == {"bootstrap_servers": "localhost:9092"}


def test_extract_defaults_by_type_fallback_to_defaults_key_and_empty_topic() -> None:
    """Verify fallback to 'defaults' key and ensures topic_or_queue is populated if missing."""
    raw_data: dict[str, Any] = {
        "defaults": [
            {
                BROKER_TYPE: "rabbitmq",
                BROKER_KWARGS: {"host": "127.0.0.1"},
                # Missing topic_or_queue
            },
            "invalid_non_dict_item",  # Should be skipped safely
        ],
    }

    _, topic_alias = _get_field_aliases()[1:]
    kwargs_alias, _, topic_alias = _get_field_aliases()

    global_default, defaults_map = _extract_defaults_by_type(raw_data)

    assert global_default == "rabbitmq"  # Default fallback when 'default' is not provided
    assert "rabbitmq" in defaults_map
    assert defaults_map["rabbitmq"][topic_alias] == ""


# ==========================================
# 3. Apply Defaults Mutation Tests
# ==========================================


def test_apply_broker_defaults_applies_global_fallback_when_type_missing() -> None:
    """Verify global default type is applied to broker dict when broker_type is missing."""
    broker_dict: dict[str, Any] = {BROKER_KWARGS: {"queue": "orders"}}
    kwargs_alias, type_alias, _ = _get_field_aliases()

    _apply_broker_defaults_to_section(
        broker_dict=broker_dict,
        global_default="rabbitmq",
        defaults_by_type={},
    )

    assert broker_dict.get(type_alias) == "rabbitmq" or broker_dict.get(BROKER_TYPE) == "rabbitmq"


def test_apply_broker_defaults_merges_kwargs_correctly() -> None:
    """Verify default kwargs are merged with thread-specific kwargs (thread kwargs priority)."""
    kwargs_alias, type_alias, _ = _get_field_aliases()

    defaults_by_type: dict[str, dict[str, Any]] = {
        "rabbitmq": {
            BROKER_KWARGS: {"host": "rabbitmq-cluster", "port": 5672},
        }
    }

    broker_dict: dict[str, Any] = {
        type_alias: "rabbitmq",
        kwargs_alias: {"port": 5673, "virtual_host": "/v1"},  # Overrides port 5672
    }

    _apply_broker_defaults_to_section(
        broker_dict=broker_dict,
        global_default="kafka",
        defaults_by_type=defaults_by_type,
    )

    resolved_kwargs = broker_dict[kwargs_alias]
    assert resolved_kwargs["host"] == "rabbitmq-cluster"
    assert resolved_kwargs["port"] == 5673  # Thread kwarg wins
    assert resolved_kwargs["virtual_host"] == "/v1"


def test_apply_broker_defaults_handles_enum_broker_type() -> None:
    """Verify enum instances in broker_type are converted to string values properly."""
    kwargs_alias, type_alias, _ = _get_field_aliases()

    defaults_by_type: dict[str, dict[str, Any]] = {
        "kafka": {
            kwargs_alias: {"security_protocol": "PLAINTEXT"},
        }
    }

    broker_dict: dict[str, Any] = {
        BROKER_TYPE: DummyBrokerEnum.KAFKA,
        kwargs_alias: {"group_id": "order_group"},
    }

    _apply_broker_defaults_to_section(
        broker_dict=broker_dict,
        global_default="rabbitmq",
        defaults_by_type=defaults_by_type,
    )

    resolved_kwargs = broker_dict[kwargs_alias]
    assert resolved_kwargs["security_protocol"] == "PLAINTEXT"
    assert resolved_kwargs["group_id"] == "order_group"
