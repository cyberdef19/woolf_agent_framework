from pydantic import BaseModel, Field


class RetryPolicy(BaseModel):
    """
    Configuration controlling repeated execution after transient failures.
    """

    max_attempts: int = Field(
        default=3,
        ge=1,
        description=(
            "Maximum total number of execution attempts, including the initial "
            "attempt."
        ),
    )

    initial_delay_seconds: float = Field(
        default=1.0,
        ge=0,
        description=(
            "Delay before the first retry attempt."
        ),
    )

    backoff_multiplier: float = Field(
        default=2.0,
        ge=1,
        description=(
            "Multiplier applied to the delay after each failed attempt."
        ),
    )

    max_delay_seconds: float = Field(
        default=30.0,
        ge=0,
        description=(
            "Maximum delay allowed between retry attempts."
        ),
    )