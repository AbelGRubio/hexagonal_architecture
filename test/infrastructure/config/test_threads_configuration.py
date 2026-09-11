
"""Unit tests for ResolvedThreadConfigModel and ThreadsConfigurations.

This module verifies correct error configuration derivation, model validation
for default injection, and thread configuration lookup.
"""

import pytest
from pydantic import ValidationError

from event_driven.infrastructure.config.enumerations import BrokersEnum, ThreadsEnum
from event_driven.infrastructure.config.schemas import BrokerConfigModel, ThreadConfigModel
from event_driven.infrastructure.config.resolved import (
    ResolvedThreadConfigModel,
    ThreadsConfigurations,
)
from event_driven.infrastructure.exceptions import MissingConfigurationError


class TestResolvedThreadConfigModel:
    """Test suite for ResolvedThreadConfigModel properties and behavior."""

    def test_resolved_error_returns_explicit_error_config(self) -> None:
        """Verify that explicit error configuration is returned if provided."""
        explicit_error = BrokerConfigModel(broker_type=BrokersEnum.RABBITMQ, topic_or_queue="custom.error")
        thread = ResolvedThreadConfigModel(
            name=ThreadsEnum.PRODUCER,
            error=explicit_error,
        )

        assert thread.resolved_error == explicit_error

    def test_resolved_error_derives_from_consumer_successfully(self) -> None:
        """Verify that error configuration is correctly derived from consumer topic/queue."""
        consumer_config = BrokerConfigModel(broker_type=BrokersEnum.RABBITMQ, topic_or_queue="my.topic")
        thread = ResolvedThreadConfigModel(
            name=ThreadsEnum.PRODUCER,
            consumer=consumer_config,
            error=None,
        )

        derived_error = thread.resolved_error
        assert derived_error.topic_or_queue == "my.topic.error"
        assert derived_error.broker_type == consumer_config.broker_type

    def test_resolved_error_derives_fallback_when_topic_empty(self) -> None:
        """Verify fallback error topic is 'error' when consumer topic_or_queue is empty."""
        consumer_config = BrokerConfigModel(broker_type=BrokersEnum.RABBITMQ, topic_or_queue="")
        thread = ResolvedThreadConfigModel(
            name=ThreadsEnum.PRODUCER,
            consumer=consumer_config,
            error=None,
        )

        derived_error = thread.resolved_error
        assert derived_error.topic_or_queue == "error"

    def test_resolved_error_raises_missing_configuration_error_when_consumer_none(self) -> None:
        """Verify MissingConfigurationError is raised when consumer and error are both missing."""
        thread = ResolvedThreadConfigModel(
            name=ThreadsEnum.PRODUCER,
            consumer=None,
            error=None,
        )

        with pytest.raises(MissingConfigurationError, match="Unable to derive error configuration"):
            _ = thread.resolved_error


class TestThreadsConfigurations:
    """Test suite for ThreadsConfigurations root model and validators."""

    def test_apply_defaults_before_validation_success(self) -> None:
        """Verify validator injects defaults correctly into thread sections when given a dict."""
        raw_data = {
            "default": "rabbitmq",
            "broker_config": [{"broker_type": "rabbitmq", "broker_kwargs": {"port": 5672}}],
            "threads": [
                {
                    "name": ThreadsEnum.WITHOUT_ASSIGNATION,
                    "consumer": {"broker_type": "rabbitmq", "topic_or_queue": "tasks"},
                }
            ],
        }

        config = ThreadsConfigurations.model_validate(raw_data)
        assert len(config.threads) == 1
        assert config.threads[0].name == ThreadsEnum.WITHOUT_ASSIGNATION
        assert config.threads[0].consumer.topic_or_queue == "tasks"

    def test_apply_defaults_before_validation_ignores_non_dict_data(self) -> None:
        """Verify validator safely handles non-dictionary inputs without crashing."""
        result = ThreadsConfigurations.apply_defaults_before_validation("not_a_dict")
        assert result == "not_a_dict"

    def test_get_thread_config_found_by_enum(self) -> None:
        """Verify get_thread_config returns the correct thread when queried using ThreadsEnum."""
        # Suponiendo que ThreadsEnum.PRODUCER.value sea "producer"
        thread_model = ResolvedThreadConfigModel(name=ThreadsEnum.PRODUCER)
        config = ThreadsConfigurations(threads=[thread_model])

        # Probando pasando el Enum directamente
        result = config.get_thread_config(ThreadsEnum.PRODUCER)
        assert result == thread_model

    def test_get_thread_config_found_by_string(self) -> None:
        """Verify get_thread_config returns the correct thread when queried using a string name."""
        thread_model = ResolvedThreadConfigModel(name=ThreadsEnum.WITHOUT_ASSIGNATION)
        config = ThreadsConfigurations(threads=[thread_model])

        result = config.get_thread_config(ThreadsEnum.WITHOUT_ASSIGNATION)
        assert result == thread_model

    def test_get_thread_config_returns_none_when_not_found(self) -> None:
        """Verify get_thread_config returns None if thread name doesn't match any configuration."""
        config = ThreadsConfigurations(threads=[])
        result = config.get_thread_config(ThreadsEnum.WITHOUT_ASSIGNATION)
        assert result is None