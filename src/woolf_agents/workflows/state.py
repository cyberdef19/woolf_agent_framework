import operator
from typing_extensions import TypedDict
from typing import Annotated
from langchain_core.messages import BaseMessage, AIMessage
from langgraph.graph.message import add_messages
from src.woolf_agents.domains.artifacts.schemas.base import PlanStepStatus, BaseTaskPlan, BaseStepResult, StepEvaluation, PlanEvaluation
from src.woolf_agents.core.result import BaseExecutionResult
from src.woolf_agents.core.result import ExecutionStatus
from typing import Literal
from src.woolf_agents.domains.artifacts.schemas.contracts import HistoricalResearchStepResult, StepExecutionContext
from enum import StrEnum

class BaseExecutionState(TypedDict, total=False):
    """
    Common execution data shared by all platform workflows and agents.
    """

    execution_id: str
    errors: list[str]
    metadata: dict[str, object]
    step_count: Annotated[int, operator.add]

class MessageAgentState(BaseExecutionState, total=False):
    """
    Base state for conversational and tool-calling agents.
    """
    messages: Annotated[list[BaseMessage], add_messages]

 

 
class PlanExecuteState(MessageAgentState, total=False):
    """Спільний Стан виконання плану агентом-планувальником"""
    plan:BaseTaskPlan
    user_task: str
    len_steps: int
    current_step_idx: Annotated[int, operator.add]
    current_step_result: BaseStepResult
    evaluated_current_step: StepEvaluation  
    revised_plans: Annotated[list[BaseTaskPlan], operator.add]
    evaluated_steps: Annotated[list[StepEvaluation], operator.add]
    results: Annotated[list[BaseStepResult], operator.add]
    structured_response: BaseExecutionResult
    execution_status: PlanStepStatus
    executor_response: AIMessage
    plan_execution_evaluated: PlanEvaluation
    human_deсision: Literal["continue","approve", "cancel"]
    interrupt_reason: str
    execution_id: str
    step_started: bool = False
    step_messages_start_idx: int
    context_step: StepExecutionContext
   
    
    