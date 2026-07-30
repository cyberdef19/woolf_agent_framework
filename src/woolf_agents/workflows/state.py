from typing_extensions import TypedDict
from typing import Annotated
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class BaseExecutionSate(TypedDict, total=False):
    """
    Common execution data shared by all platform workflows and agents.
    """

    execution_id: str
    errors: list[str]
    metadata: dict[str, object]
    step_count: int

class MessageAgentState(BaseExecutionSate, total=False):
    """
    Base state for conversational and tool-calling agents.
    """

    messages: Annotated[list[BaseMessage], add_messages]