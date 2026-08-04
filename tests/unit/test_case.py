# evaluation/contracts.py

from pydantic import BaseModel, ConfigDict, Field

class TestExpectation(BaseModel):
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
    expectation: TestExpectation = Field(
        default_factory=TestExpectation,
    )