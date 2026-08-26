"""Resolved for thread config model."""
from typing import Any, get_args

from event_driven.infrastructure.config.schemas import ThreadConfigModel, BrokerConfigModel


BROKER_KWARGS = "broker_kwargs"
BROKER_TYPE = "broker_type"
TOPIC_OR_QUEUE = "topic_or_queue"

# ==============================================================================
# Helper Functions (Modularized Business Logic)
# ==============================================================================

def _get_field_aliases() -> tuple[str, str, str]:
    """Retrieves field aliases for broker kwargs, type, and topic."""
    kwargs_alias = BrokerConfigModel.model_fields[BROKER_KWARGS].alias or BROKER_KWARGS
    type_alias = BrokerConfigModel.model_fields[BROKER_TYPE].alias or BROKER_TYPE
    topic_alias = BrokerConfigModel.model_fields[TOPIC_OR_QUEUE].alias or TOPIC_OR_QUEUE
    return kwargs_alias, type_alias, topic_alias


def _extract_defaults_by_type(raw_data: dict[str, Any]) -> tuple[str, dict[str, dict[str, Any]]]:
    """Extracts the global default broker type and builds a lookup map for broker configs."""
    kwargs_alias, type_alias, topic_alias = _get_field_aliases()

    # 1. Global default broker type
    global_default = str(raw_data.get("default", "rabbitmq")).lower()

    # 2. Extract broker defaults list
    broker_config_list = raw_data.get("broker_config") or raw_data.get("defaults") or []
    defaults_by_type: dict[str, dict[str, Any]] = {}

    if isinstance(broker_config_list, list):
        for default_item in broker_config_list:
            if not isinstance(default_item, dict):
                continue

            # Ensure topic_or_queue is not null
            if not default_item.get(TOPIC_OR_QUEUE) and not default_item.get(topic_alias):
                default_item[topic_alias] = ""

            b_type = default_item.get(BROKER_TYPE) or default_item.get(type_alias)
            if b_type:
                b_type_str = b_type.value if hasattr(b_type, "value") else str(b_type)
                defaults_by_type[b_type_str.lower()] = default_item

    return global_default, defaults_by_type


def _get_broker_section_names() -> list[str]:
    """Finds all field names in ThreadConfigModel that are of type BrokerConfigModel."""
    broker_sections = []
    for field_name, field_info in ThreadConfigModel.model_fields.items():
        args = get_args(field_info.annotation)
        if BrokerConfigModel in args or field_info.annotation is BrokerConfigModel:
            broker_sections.append(field_name)
    return broker_sections


def _apply_broker_defaults_to_section(
        broker_dict: dict[str, Any],
        global_default: str,
        defaults_by_type: dict[str, dict[str, Any]]
) -> None:
    """Mutates a single broker dict by applying fallback types and merging broker_kwargs."""
    kwargs_alias, type_alias, _ = _get_field_aliases()

    # Determine broker type or use global fallback
    broker_type_val = broker_dict.get(BROKER_TYPE) or broker_dict.get(type_alias)
    if not broker_type_val:
        broker_type_str = global_default
        broker_dict[type_alias] = global_default
    else:
        broker_type_str = broker_type_val.value if hasattr(broker_type_val, "value") else str(broker_type_val)

    # Merge kwargs if a default configuration exists
    matched_default = defaults_by_type.get(broker_type_str.lower())
    if matched_default:
        default_kwargs = matched_default.get(BROKER_KWARGS) or matched_default.get(kwargs_alias) or {}
        thread_kwargs = broker_dict.get(BROKER_KWARGS) or broker_dict.get(kwargs_alias) or {}

        if isinstance(default_kwargs, dict) and isinstance(thread_kwargs, dict):
            broker_dict[kwargs_alias] = {**default_kwargs, **thread_kwargs}
