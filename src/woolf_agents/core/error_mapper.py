from errors import ErrorInfo, ErrorSeverity
from exceptions import BaseFrameworkException


def error_info_from_exception(
    error: BaseFrameworkException,
    *,
    source: str | None = None,
    severity: ErrorSeverity = ErrorSeverity.ERROR,
) -> ErrorInfo:
    """
    Convert a platform exception into its structured serializable form.
    """

    return ErrorInfo(
        code=error.code,
        message=error.message,
        severity=severity,
        recoverable=error.recoverable,
        source=source,
        context=error.context,
    )