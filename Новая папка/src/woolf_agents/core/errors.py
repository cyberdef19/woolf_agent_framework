from datetime import datetime, timezone
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, ConfigDict


class ErrorSeverity(StrEnum):
    """Severity level assigned to a recorded error."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ErrorInfo(BaseModel):
    """
    Structured and serializable representation of an execution error.

    The model can be used in execution results, structured logs, audit events,
    API responses, and sanitized feedback provided to an LLM.

    It represents information about an error and does not replace the original
    Python exception used for runtime flow control.
    """
    model_config = ConfigDict(
        extra="forbid"
    )
    
    retrayable: bool = Field(
        default_factory=False,
        description="Indicates whether the failed operation may succeed if it is "
                    "executed again. A value of 'true' means the runtime may retry the "
                    "operation according to the configured retry policy. A value of "
                    "'false' means that repeating the same operation without changing "
                    "its inputs or configuration is not expected to resolve the error."
    )
    
    error_id: UUID = Field(
        default_factory=uuid4,
        description=(
            "Unique identifier of this error occurrence. The identifier may be "
            "used to correlate execution results, logs, traces, and audit events."
        ),
    )

    code: str = Field(
        description=(
            "Stable machine-readable identifier of the error category, such as "
            "'TOOL_TIMEOUT', 'INVALID_CONFIGURATION', or "
            "'STRUCTURED_OUTPUT_VALIDATION_FAILED'."
        ),
    )

    message: str = Field(
        description=(
            "Sanitized human-readable explanation of the error. The value must "
            "not contain credentials, access tokens, stack traces, personal "
            "information, or other sensitive implementation details."
        ),
    )

    severity: ErrorSeverity = Field(
        default=ErrorSeverity.ERROR,
        description=(
            "Severity of the recorded error used for logging, alerting, and "
            "execution-policy decisions."
        ),
    )

    recoverable: bool = Field(
        default=False,
        description=(
            "Indicates whether the workflow may recover by retrying the "
            "operation, changing its arguments, selecting a fallback, or "
            "continuing with a partial result."
        ),
    )

    source: str | None = Field(
        default=None,
        description=(
            "Logical platform component in which the error originated, such as "
            "'llm.openrouter', 'tools.web_search', or "
            "'assignment_01.workflow'."
        ),
    )

    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp indicating when the error was recorded.",
    )

    context: dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "Sanitized structured context useful for diagnostics and auditing. "
            "Sensitive values and raw external payloads must not be stored."
        ),
    )
    
    attempt: int | None = Field(
        default=None,
        ge=1,
        description=(
            "Number of the execution attempt during which the error occurred."
        ),
    )

    max_attempts: int | None = Field(
        default=None,
        ge=1,
        description=(
            "Maximum number of attempts allowed by the active retry policy."
        ),
    )

    retry_delay_seconds: float | None = Field(
        default=None,
        ge=0,
        description=(
            "Delay before the next retry, or null when no further retry is "
            "scheduled."
        ),
    )