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


class NotValidOperativeError(BaseCustomError):
    """The operative is not valid."""

    def __init__(
        self,
        message: str = "",
        code: str | int = "",
        description: str = "The operative is not valid.",
    ) -> None:
        """Initialize exception."""
        super().__init__(
            message=message,
            code=code,
            description=description,
        )
