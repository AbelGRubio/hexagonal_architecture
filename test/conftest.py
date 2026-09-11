import pytest
from unittest.mock import patch, MagicMock

@pytest.fixture(autouse=True)
def mock_broker_pybreaker_globally():
    """Mockea broker_pybreaker automáticamente en todos los tests."""
    with patch("event_driven.infrastructure.config.init_pybreaker.broker_pybreaker") as mock_broker:
        # Configura un mock por defecto si es necesario
        mock_broker.return_value = MagicMock()
        yield mock_broker



@pytest.fixture(autouse=True)
def mock_external_brokers_globally():
    """Mockea Redis y Pybreaker globalmente para evitar conexiones reales en los tests."""
    with patch("redis.Redis") as mock_redis, \
            patch("pybreaker.CircuitBreaker") as mock_cb, \
            patch("pybreaker.CircuitRedisStorage") as mock_storage:
        # Configuramos comportamientos por defecto para que no devuelvan None
        mock_redis.return_value = MagicMock()
        mock_cb.return_value = MagicMock()
        mock_storage.return_value = MagicMock()

        yield