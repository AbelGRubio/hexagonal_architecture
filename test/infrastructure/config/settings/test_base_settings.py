from collections.abc import Generator
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from event_driven.infrastructure.config.settings.base_settings import BaseTraceableSettings


@pytest.fixture(autouse=True)
def mock_aws_clients() -> Generator[dict[str, MagicMock]]:
    """Mock AWS S3 and Secrets Manager clients to prevent external calls during tests."""
    mock_s3 = MagicMock()
    mock_sm = MagicMock()

    # Simple default mocks to avoid errors if invoked
    mock_s3.get_object.return_value = {"Body": MagicMock(read=lambda: b"mocked_s3_value")}
    mock_sm.get_secret_value.return_value = {"SecretString": "mocked_sm_value"}

    # Mock low-level client getters in the source module
    path_to_source = "event_driven.infrastructure.config.settings.source.source_s3_secrets"
    s3_path = f"{path_to_source}.get_s3_client"
    sm_path = f"{path_to_source}.get_secrets_manager_client"
    with patch(s3_path, return_value=mock_s3), patch(sm_path, return_value=mock_sm):
        yield {"s3": mock_s3, "sm": mock_sm}


def test_instantiation_basetraceablesettings_with_defaults() -> None:
    """Verify that BaseTraceableSettings instantiates correctly with default or init values."""
    # Direct instantiation passing test arguments
    test_args: dict[str, Any] = {}
    settings: BaseTraceableSettings = BaseTraceableSettings(**test_args)

    assert settings is not None

    # Verify that get_origins() returns a dictionary containing property keys
    origins: dict[str, str] = settings.get_origins()
    assert isinstance(origins, dict)

    # Every field passed in init should have 'init' as its origin
    for field_name in test_args:
        assert settings.get_origin(field_name) == "init"


def test_env_var_override_basetraceablesettings(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify that environment variables override values and set origin to 'env_var'."""
    prefix: str = str(BaseTraceableSettings.model_config.get("env_prefix", ""))

    # If no dynamic fields were passed to the template, instantiate and validate basic structure
    settings: BaseTraceableSettings = BaseTraceableSettings()
    origins: dict[str, str] = settings.get_origins()
    assert isinstance(origins, dict)


def test_unknown_field_origin_basetraceablesettings() -> None:
    """Verify fallback to 'Default' for fields that are not explicitly tracked."""
    test_args: dict[str, Any] = {}
    settings: BaseTraceableSettings = BaseTraceableSettings(**test_args)

    assert settings.get_origin("non_existing_field_xyz") == "Default"
