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


class ConfigurationError(BaseCustomError):
    """The configuration doesn't load correctly."""

    def __init__(
        self,
        message: str = "No configuration loaded property",
        code: str | int = "",
        description: str = "The configuration doesn't load correctly.",
    ) -> None:
        """Initialize exception."""
        super().__init__(
            message=message,
            code=code,
            description=description,
        )
