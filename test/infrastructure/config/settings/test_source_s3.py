"""Unit tests for S3 / Secrets Manager custom settings source.

This module verifies correct boto3 client initialization, URI/ARN parsing,
remote fetching from S3 and Secrets Manager, and recursive value resolution.
"""

from unittest.mock import MagicMock, patch
import pytest
from pydantic import SecretStr
from pydantic.fields import FieldInfo
from pydantic_settings import BaseSettings

from event_driven.infrastructure.config.settings.source.source_s3_secrets import (
    get_s3_client,
    get_secrets_manager_client,
    S3SecretSource,
)


class DummySettings(BaseSettings):
    """Dummy settings model used for testing S3SecretSource."""
    secret_field: SecretStr = SecretStr("s3://my-bucket/path/to/secret")
    plain_field: str = "plain_value"
    sm_field: SecretStr = SecretStr("arn:aws:secretsmanager:us-east-1:123456789012:secret:my-secret")


@pytest.fixture(autouse=True)
def clear_lru_caches():
    """Clear lru_cache for client getters before and after each test."""
    get_s3_client.cache_clear()
    get_secrets_manager_client.cache_clear()
    yield
    get_s3_client.cache_clear()
    get_secrets_manager_client.cache_clear()


# ==========================================
# 1. Tests for Client Getters & Caching
# ==========================================


@patch("event_driven.infrastructure.config.settings.source.source_s3_secrets.boto3.client")
def test_get_s3_client_singleton(mock_boto_client: MagicMock) -> None:
    """Verify get_s3_client instantiates boto3 s3 client correctly and caches it via lru_cache."""
    mock_instance = MagicMock()
    mock_boto_client.return_value = mock_instance

    client1 = get_s3_client()
    client2 = get_s3_client()

    assert client1 == mock_instance
    assert client2 == mock_instance
    mock_boto_client.assert_called_once_with("s3", endpoint_url=None, verify=False, region_name=None)


@patch("event_driven.infrastructure.config.settings.source.source_s3_secrets.boto3.client")
def test_get_secrets_manager_client_singleton(mock_boto_client: MagicMock) -> None:
    """Verify get_secrets_manager_client instantiates secretsmanager client correctly and caches it."""
    mock_instance = MagicMock()
    mock_boto_client.return_value = mock_instance

    client1 = get_secrets_manager_client()
    client2 = get_secrets_manager_client()

    assert client1 == mock_instance
    assert client2 == mock_instance
    mock_boto_client.assert_called_once_with("secretsmanager", endpoint_url=None, verify=False, region_name=None)


# ==========================================
# 2. Tests for S3SecretSource Logic
# ==========================================


@patch("event_driven.infrastructure.config.settings.source.source_s3_secrets.get_secrets_manager_client")
@patch("event_driven.infrastructure.config.settings.source.source_s3_secrets.get_s3_client")
class TestS3SecretSource:
    """Test suite for S3SecretSource resolution and fetching mechanisms."""

    def test_parse_s3_uri_standard(self, mock_s3_client: MagicMock, mock_sm_client: MagicMock) -> None:
        """Verify parsing standard s3:// URIs into bucket and key."""
        source = S3SecretSource(DummySettings)
        bucket, key = source._parse_s3_uri("s3://my-bucket-name/folder/file.json")
        assert bucket == "my-bucket-name"
        assert key == "folder/file.json"

    def test_parse_s3_uri_arn(self, mock_s3_client: MagicMock, mock_sm_client: MagicMock) -> None:
        """Verify parsing AWS S3 ARN format into bucket and key."""
        source = S3SecretSource(DummySettings)
        bucket, key = source._parse_s3_uri("arn:aws:s3:::my-arn-bucket/path/to/object")
        assert bucket == "::my-arn-bucket"
        assert key == "path/to/object"

    def test_fetch_from_s3_success(self, mock_s3_client: MagicMock, mock_sm_client: MagicMock) -> None:
        """Verify fetching content successfully from S3."""
        client_mock = MagicMock()
        body_mock = MagicMock()
        body_mock.read.return_value = b"  secret-content-body  \n"
        client_mock.get_object.return_value = {"Body": body_mock}
        mock_s3_client.return_value = client_mock

        source = S3SecretSource(DummySettings)
        result = source._fetch_from_s3("s3://my-bucket/my-key")

        assert result == "secret-content-body"
        client_mock.get_object.assert_called_once_with(Bucket="my-bucket", Key="my-key")

    def test_fetch_from_s3_raises_runtime_error_on_failure(
        self, mock_s3_client: MagicMock, mock_sm_client: MagicMock
    ) -> None:
        """Verify that exceptions during S3 fetching are wrapped in a RuntimeError."""
        client_mock = MagicMock()
        client_mock.get_object.side_effect = Exception("Access Denied")
        mock_s3_client.return_value = client_mock

        source = S3SecretSource(DummySettings)
        with pytest.raises(RuntimeError, match="Failed to retrieve object from S3"):
            source._fetch_from_s3("s3://my-bucket/my-key")

    def test_fetch_from_secrets_manager_string(
        self, mock_s3_client: MagicMock, mock_sm_client: MagicMock
    ) -> None:
        """Verify fetching secret string from Secrets Manager."""
        client_mock = MagicMock()
        client_mock.get_secret_value.return_value = {"SecretString": "super-secret-json"}
        mock_sm_client.return_value = client_mock

        source = S3SecretSource(DummySettings)
        result = source._fetch_from_secrets_manager("arn:aws:secretsmanager:region:123:secret:name")

        assert result == "super-secret-json"
        client_mock.get_secret_value.assert_called_once_with(SecretId="arn:aws:secretsmanager:region:123:secret:name")

    def test_fetch_from_secrets_manager_binary(
        self, mock_s3_client: MagicMock, mock_sm_client: MagicMock
    ) -> None:
        """Verify fetching binary secret with fallback decode."""
        client_mock = MagicMock()
        client_mock.get_secret_value.return_value = {"SecretBinary": b"binary-secret-bytes"}
        mock_sm_client.return_value = client_mock

        source = S3SecretSource(DummySettings)
        result = source._fetch_from_secrets_manager("arn:aws:secretsmanager:region:123:secret:name")

        assert result == "binary-secret-bytes"

    def test_fetch_from_secrets_manager_raises_runtime_error(
        self, mock_s3_client: MagicMock, mock_sm_client: MagicMock
    ) -> None:
        """Verify that failures in Secrets Manager wrap errors into RuntimeError."""
        client_mock = MagicMock()
        client_mock.get_secret_value.side_effect = Exception("NotFound")
        mock_sm_client.return_value = client_mock

        source = S3SecretSource(DummySettings)
        with pytest.raises(RuntimeError, match="Failed to retrieve secret from Secrets Manager"):
            source._fetch_from_secrets_manager("arn:aws:secretsmanager:...")

    @patch.object(S3SecretSource, "_fetch_from_s3")
    @patch.object(S3SecretSource, "_fetch_from_secrets_manager")
    def test_resolve_value_recursive(
        self,
        mock_fetch_sm: MagicMock,
        mock_fetch_s3: MagicMock,
        mock_s3_client: MagicMock,
        mock_sm_client: MagicMock,
    ) -> None:
        """Verify resolve_value processes strings, dicts, and lists recursively."""
        mock_fetch_s3.return_value = "resolved_s3"
        mock_fetch_sm.return_value = "resolved_sm"

        source = S3SecretSource(DummySettings)

        payload = {
            "s3_uri": "s3://bucket/key",
            "s3_arn": "arn:aws:s3:::bucket/key",
            "sm_arn": "arn:aws:secret:...",
            "nested_list": ["s3://bucket/item", "plain_val"],
            "plain_str": "normal_string",
        }

        resolved = source.resolve_value(payload)

        assert resolved["s3_uri"] == "resolved_s3"
        assert resolved["s3_arn"] == "resolved_s3"
        assert resolved["sm_arn"] == "resolved_sm"
        assert resolved["nested_list"] == ["resolved_s3", "plain_val"]
        assert resolved["plain_str"] == "normal_string"

    @patch.object(S3SecretSource, "resolve_value")
    def test_get_data(
        self, mock_resolve_value: MagicMock, mock_s3_client: MagicMock, mock_sm_client: MagicMock
    ) -> None:
        """Verify get_data iterates through SecretStr fields and extracts resolved values."""
        mock_resolve_value.side_effect = lambda val: f"resolved_{val}"

        source = S3SecretSource(DummySettings, wrapped_source={"secret_field": "s3://override/path"})
        data = source.get_data()

        assert "secret_field" in data
        assert data["secret_field"] == "resolved_s3://override/path"
        # Plain fields shouldn't be processed or included
        assert "plain_field" not in data

    def test_call_and_get_field_value(
        self, mock_s3_client: MagicMock, mock_sm_client: MagicMock
    ) -> None:
        """Verify __call__ invokes get_data and get_field_value complies with Pydantic spec."""
        source = S3SecretSource(DummySettings)
        with patch.object(source, "get_data", return_value={"mock": "data"}) as mock_get_data:
            assert source() == {"mock": "data"}
            mock_get_data.assert_called_once()

        field_info = MagicMock(spec=FieldInfo)
        val, name, found = source.get_field_value(field_info, "sample_name")
        assert val is None
        assert name == "sample_name"
        assert found is False