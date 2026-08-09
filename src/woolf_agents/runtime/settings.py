
from pathlib import Path
from pydantic import BaseModel, Field


class AgentRuntimeSettings(BaseModel):
    """Runtime limits and observability settings for an agent workflow."""

    max_steps: int = Field(
        default=6,
        ge=1,
        description=(
            "Maximum number of LLM iterations allowed by "
            "the StopController."
        ),
    )

    max_tokens: int = Field(
        default=50_000,
        ge=1,
        description="Maximum cumulative token usage for one run.",
    )

    timeout_seconds: float = Field(
        default=240.0,
        gt=0,
        description="Maximum wall-clock duration of the complete run.",
    )

    max_repeats: int = Field(
        default=3,
        ge=2,
        description=(
            "Maximum number of consecutive identical tool calls."
        ),
    )

    recursion_limit: int = Field(
        default=30,
        ge=1,
        description=(
            "Emergency LangGraph super-step limit for one execution."
        ),
    )

    trajectory_logging_enabled: bool = True

    trajectory_log_directory: Path = Path(
        "logs/trajectories"
    )