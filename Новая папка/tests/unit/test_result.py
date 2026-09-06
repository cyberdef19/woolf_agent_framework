from typing import Any

from pydantic import BaseModel, Field


class ToolCallRecord(BaseModel):
    """One tool call observed during graph execution."""

    name: str
    arguments: dict[str, Any] = Field(
        default_factory=dict,
    )


class AgentTestResult(BaseModel):
    """Collected result and metrics for one test case."""

    case_id: str

    input_query: str

    expected_result: str

    actual_result: Any = None

    passed: bool = False

    execution_status: str

    step_count: int = 0

    tool_calls: list[ToolCallRecord] = Field(
        default_factory=list,
    )

    execution_time_seconds: float = 0.0

    used_tokens: int = 0

    error: str | None = None