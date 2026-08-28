import operator
from typing_extensions import TypedDict
from typing import Annotated
from langchain_core.messages import BaseMessage, AIMessage
from langgraph.graph.message import add_messages
from src.woolf_agents.domains.artifacts.schemas.base import PlanStepStatus, BaseTaskPlan, BaseStepResult, StepEvaluation, PlanEvaluation
from src.woolf_agents.core.result import BaseExecutionResult
from src.woolf_agents.core.result import ExecutionStatus
from typing import Literal
from src.woolf_agents.domains.artifacts.schemas.contracts import (
                                               PlanStepStatus, 
                                               HistoricalResearchStepResult,
                                               HistoricalHypothesisEvaluationPlan, 
                                               HistoricalResearchStepPlan,
                                               HypothesisEvaluationStep,
                                               HistoricalResearchPlan,
                                               StepExecutionContext)
from src.woolf_agents.runtime.stop_controller import StopDecision
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

class AnalysisStatus(StrEnum):
        PENDING = "pending"
        INPROGRESS ="in_progress"
        COMPLETED ="completed"
        FAILED = "failed"
        STOPPED ="stopped"

 

class ToolGraphState(MessageAgentState, total=False):
    """Стан ReAct агента для виклику інструментів """
    execution_id: int    
    execution_status: AnalysisStatus
    summary: str
    used_tokens: int 
    step_count: Annotated[int, operator.add]
    tool_call_history: Annotated[list[str], operator.add]
    structured_reponse: BaseStepResult
    stop_decision: StopDecision

class PlanExecuteStatus(StrEnum):
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    READY_FOR_PLAN_EVALUATION = "ready_for_plan_evaluation"
    REPLANNING = "replanning"
    WAITTING_FOR_HUMAN = "waitting_for_human"
 
class PlanExecuteState(MessageAgentState, total=False):
    """Стан виконання плану агентом-планувальником"""
    plan:HistoricalHypothesisEvaluationPlan
    user_task: str
    len_steps: int
    current_step_idx: Annotated[int, operator.add]
    current_step_result: HistoricalResearchStepResult|None
    evaluated_current_step: StepEvaluation  
    revised_plans: Annotated[list[HistoricalHypothesisEvaluationPlan], operator.add]
    evaluated_steps: Annotated[list[StepEvaluation], operator.add]
    results: Annotated[list[HistoricalResearchStepResult], operator.add]
    structured_response: BaseExecutionResult
    execution_status: PlanExecuteStatus
    executor_response: AIMessage
    plan_execution_evaluated: PlanEvaluation| None
    human_deсision: Literal["continue","approve", "cancel"]
    interrupt_reason: str
    execution_id: str
    step_started: bool = False
    step_messages_start_idx: int
    context_step: StepExecutionContext
    step_status: PlanStepStatus
   
    
    