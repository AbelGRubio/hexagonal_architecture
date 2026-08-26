"""Resolved for thread config model."""
from typing import Any

from pydantic import Field, model_validator, BaseModel

from event_driven.infrastructure.config.enumerations import BrokersEnum
from event_driven.infrastructure.config.schemas import ThreadConfigModel, BrokerConfigModel
from event_driven.infrastructure.config.utils import _extract_defaults_by_type, _apply_broker_defaults_to_section, \
    _get_broker_section_names
from event_driven.infrastructure.exceptions import MissingConfigurationError


# ==============================================================================
# Main Pydantic Models
# ==============================================================================

class ResolvedThreadConfigModel(ThreadConfigModel):
    """Extends the auto-generated config model by resolving default fallbacks and enforcing rules."""

    @property
    def resolved_error(self) -> BrokerConfigModel:
        """Returns the explicit error configuration or derives it from the consumer.

        Raises:
            ValueError: If consumer configuration is missing and error config cannot be derived.
        """
        # 1. Use explicit error config if provided
        if self.error is not None:
            return self.error

        # 2. Raise explicit error if consumer is missing
        if self.consumer is None:
            thread_info = f" for thread '{self.name}'" if self.name else ""
            message = (
                f"Invalid configuration{thread_info}: Unable to derive error configuration "
                "because 'consumer' configuration is missing."
            )
            raise MissingConfigurationError(message=message)

        # 3. Derive error queue/topic from consumer
        consumer_topic = self.consumer.topic_or_queue
        error_topic = f"{consumer_topic}.error" if consumer_topic else "error"

        return self.consumer.model_copy(
            update={"topic_or_queue": error_topic}
        )


class ThreadsConfigurations(BaseModel):
    """Root configuration mapping the threads.yaml structure."""

    default: BrokersEnum = Field(default=BrokersEnum.RABBITMQ, alias="default")
    broker_config: list[BrokerConfigModel] = Field(default_factory=list, alias="broker_config")
    threads: list[ResolvedThreadConfigModel] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def apply_defaults_before_validation(cls, data: Any) -> Any:
        """Orchestrates default injection into each thread's broker configuration."""
        if not isinstance(data, dict):
            return data

        global_default, defaults_by_type = _extract_defaults_by_type(data)
        broker_sections = _get_broker_section_names()
        threads_data = data.get("threads", [])

        if isinstance(threads_data, list):
            for thread in threads_data:
                if not isinstance(thread, dict):
                    continue

                for section in broker_sections:
                    section_alias = ThreadConfigModel.model_fields[section].alias or section
                    broker_dict = thread.get(section) or thread.get(section_alias)

                    if isinstance(broker_dict, dict):
                        _apply_broker_defaults_to_section(broker_dict, global_default, defaults_by_type)

        return data

if __name__ == '__main__':
    import yaml
    from pathlib import Path

    path = Path("../../../../../pymodeller/threads.yaml")

    if path.exists():
        with open(path, "r", encoding="utf-8") as file:
            raw_data: dict[str, Any] = yaml.safe_load(file) or {}

        # Carga automática limpia en una sola línea
        config = ThreadsConfigurations.model_validate(raw_data)

        print(f"Cargados {len(config.threads)} hilos correctamente.")
        for t in config.threads:
            print(f"- Thread: {t.name}")
            if t.consumer:
                print(
                    f"  Consumer: {t.consumer.broker_type} -> {t.consumer.topic_or_queue} (Kwargs: {t.consumer.broker_kwargs})")
            if t.resolved_error:
                print(f"  Error: {t.resolved_error.broker_type} -> {t.resolved_error.topic_or_queue} (Kwargs: {t.resolved_error.broker_kwargs})")

    f = 1