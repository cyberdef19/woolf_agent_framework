from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field
from assignments.assignment_01.state import Assignment01AgentState

class AgentTestExpectation(BaseModel):
    """Machine-checkable expectations for one evaluation case."""

    required_tools: tuple[str, ...] = ()
    forbidden_tools: tuple[str, ...] = ()
    expected_status: str = "completed"
    expected_content: tuple[str, ...] = ()

class AgentTestCase(BaseModel):
    """Input and expected behavior for one agent evaluation case."""

    model_config = ConfigDict(frozen=True)

    case_id: str = Field(
        min_length=1,
        description="Unique identifier of the test case.",
    )

    artifact_path:Path = Field(
        default_factory=None,
        description="Шлях до досліджуваного файла у системі"
    )
    input_query: str = Field(
        min_length=1,
        description="User query passed to the agent workflow.",
    )

    expected_result: str = Field(
        min_length=1,
        description=(
            "Human-readable description of the expected behavior "
            "or expected output."
        ),
    )
    expectation: AgentTestExpectation = Field(
        default_factory=AgentTestExpectation,
    )