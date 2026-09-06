from collections.abc import Sequence
from typing import Any

from langchain_core.messages import AIMessage
from .test_result import ToolCallRecord
from .test_case import AgentTestCase


def extract_tool_calls(
    messages: Sequence[Any],
) -> list[ToolCallRecord]:
    """Extract all tool calls from accumulated AI messages."""

    records: list[ToolCallRecord] = []

    for message in messages:
        if not isinstance(message, AIMessage):
            continue

        for tool_call in message.tool_calls:
            records.append(
                ToolCallRecord(
                    name=tool_call["name"],
                    arguments=tool_call.get(
                        "args",
                        {},
                    ),
                )
            )

    return records

from typing import Any


def evaluate_test_result(
    *,
    test_case: AgentTestCase,
    final_state: dict[str, Any],
    tool_calls: list[ToolCallRecord],
) -> bool:
    """Evaluate machine-checkable expectations."""

    expectation = test_case.expectation

    actual_tool_names = {
        tool_call.name
        for tool_call in tool_calls
    }

    required_tools_present = all(
        tool_name in actual_tool_names
        for tool_name in expectation.required_tools
    )

    forbidden_tools_absent = all(
        tool_name not in actual_tool_names
        for tool_name in expectation.forbidden_tools
    )

    status_matches = (
        final_state.get("execution_status")
        == expectation.expected_status
    )

    actual_result = final_state.get(
        "structured_response"
    )

    actual_text = str(actual_result).lower()

    content_matches = all(
        fragment.lower() in actual_text
        for fragment in expectation.expected_content
    )

    return all(
        (
            required_tools_present,
            forbidden_tools_absent,
            status_matches,
            content_matches,
        )
    )