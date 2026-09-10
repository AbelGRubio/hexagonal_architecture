"""AUTO-GENERATED EXCEPTIONS."""


class BaseCustomError(Exception):
    """Base custom exception."""

    def __init__(
        self,
        message: str = "General exception.",
        code: str | int = "GENERAL_ERROR",
        description: str = "General exception raised.",
    ) -> None:
        """Initialize exception."""
        super().__init__(message)
        self.message = message
        self.code = code
        self.description = description


class BrokerNotFoundError(BaseCustomError):
    """Broker not found, please select a valid one."""

    def __init__(
        self,
        message: str = "",
        code: str | int = "",
        description: str = "Broker not found, please select a valid one.",
    ) -> None:
        """Initialize exception."""
        super().__init__(
            message=message,
            code=code,
            description=description,
        )


class ConfigurationError(BaseCustomError):
    """The configuration doesn't load correctly."""

    def __init__(
        self,
        message: str = "",
        code: str | int = "",
        description: str = "The configuration doesn't load correctly.",
    ) -> None:
        """Initialize exception."""
        super().__init__(
            message=message,
            code=code,
            description=description,
        )


class MissingConfigurationError(BaseCustomError):
    """Unable to get the configuration."""

    def __init__(
        self,
        message: str = "",
        code: str | int = "",
        description: str = "Unable to get the configuration.",
    ) -> None:
        """Initialize exception."""
        super().__init__(
            message=message,
            code=code,
            description=description,
        )
