"""Unit tests for custom domain exceptions.

This test suite validates default values, attribute assignments,
custom parameter overrides, and class inheritance hierarchies.
"""

import pytest

from event_driven.domain.exceptions.exceptions import BaseCustomError, NotValidOperativeError


# ==========================================
# 1. BaseCustomError Tests
# ==========================================


def test_base_custom_error_default_initialization() -> None:
    """Verify BaseCustomError sets standard default attributes."""
    error = BaseCustomError()

    assert str(error) == "General exception."
    assert error.message == "General exception."
    assert error.code == "GENERAL_ERROR"
    assert error.description == "General exception raised."
    assert isinstance(error, Exception)


def test_base_custom_error_custom_initialization() -> None:
    """Verify BaseCustomError accepts custom message, code, and description."""
    custom_message = "Custom failure occurred"
    custom_code = 500
    custom_description = "Detailed failure description"

    error = BaseCustomError(
        message=custom_message,
        code=custom_code,
        description=custom_description,
    )

    assert str(error) == custom_message
    assert error.message == custom_message
    assert error.code == custom_code
    assert error.description == custom_description


# ==========================================
# 2. NotValidOperativeError Tests
# ==========================================


def test_not_valid_operative_error_default_initialization() -> None:
    """Verify NotValidOperativeError sets its specific default attributes."""
    error = NotValidOperativeError()

    assert str(error) == "No valid operative loaded property"
    assert error.message == "No valid operative loaded property"
    assert error.code == ""
    assert error.description == "The operative is not valid."
    assert isinstance(error, BaseCustomError)
    assert isinstance(error, Exception)


def test_not_valid_operative_error_custom_initialization() -> None:
    """Verify NotValidOperativeError allows overriding default arguments."""
    custom_message = "Invalid operation for current context"
    custom_code = "INVALID_OPERATIVE_CODE"
    custom_description = "Operative validation failed during execution."

    error = NotValidOperativeError(
        message=custom_message,
        code=custom_code,
        description=custom_description,
    )

    assert str(error) == custom_message
    assert error.message == custom_message
    assert error.code == custom_code
    assert error.description == custom_description


def test_exception_raising_and_catching() -> None:
    """Verify exceptions can be raised and caught properly via pytest.raises."""
    with pytest.raises(NotValidOperativeError) as exc_info:
        raise NotValidOperativeError(message="Raised error", code="ERR_100")

    raised_error = exc_info.value
    assert raised_error.message == "Raised error"
    assert raised_error.code == "ERR_100"