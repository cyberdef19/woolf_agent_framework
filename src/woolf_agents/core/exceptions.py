from typing import Any

class BaseFrameworkException(Exception):
    """
    Base exception for all platform-specific errors.

    Application code may catch this exception when it needs to handle any
    error produced by the Woolf Agent Platform without intercepting unrelated
    Python exceptions.
    """
    default_code = "BaseFramework_ERROR"
    default_retry = False

    def __init__(
        self,
        message: str,
        *,
        code: str | None = None,
        context: dict[str, Any] | None = None,
        recoverable: bool = False,
        retryable: bool | None = None
    ) -> None:
        super().__init__(message)

        self.message = message
        self.code = code or self.default_code
        self.context = context or {}
        self.recoverable = recoverable
        self.retryable = (
            self.default_retry 
            if retryable is None
            else retryable
        )
        

class IntegrationError(BaseFrameworkException):
    """
    Raised when an operation involving an external service, provider,
    database, API, or infrastructure component fails.
    """
    default_code = "IntegrationError"

class ConfigurationError(BaseFrameworkException):
    """Raised when platform configuration is missing or invalid."""

    default_code = "CONFIGURATION_ERROR"