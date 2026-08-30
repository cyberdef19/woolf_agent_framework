from collections.abc import Sequence

from src.woolf_agents.runtime.settings import AgentRuntimeSettings
from src.woolf_agents.runtime.trajectory_logger import TrajectoryLogger
from .tool_calling_graph import ToolCallingGraph
from src.woolf_agents.runtime.runner import AgentGraphRunner
from typing import TypeVar, Generic
from src.woolf_agents.llm.executor import LLMExecutor
from src.woolf_agents.domains.artifacts.schemas.contracts import HistoricalResearchStepResult, StepExecutionContext
from src.woolf_agents.domains.artifacts.schemas.base import BaseStepResult
from src.woolf_agents.runtime.stop_controller import StopController
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.tools import BaseTool
from langchain.messages import HumanMessage
from langgraph.checkpoint.base import BaseCheckpointSaver
from .state import ToolGraphState ,AnalysisStatus

from uuid import uuid4 

StateT = TypeVar("StateT")
OutputT = TypeVar("OutputT")

class ToolCallingWorker(Generic[StateT, OutputT]):
    
    def __init__(self,
                 state: StateT,
                 llm: BaseChatModel,
                 tools: Sequence[BaseTool],
                 output_schema: OutputT,
                 system_prompt: str,
                 executor: LLMExecutor,
                 stop_controller: StopController,
                 checkpointer: BaseCheckpointSaver,
                 ):
        super().__init__()
        self._compiled_tool_calling: ToolCallingGraph = ToolCallingGraph(
            state=state,
            model=llm,
            tools=tools,
            output_schema=HistoricalResearchStepResult,
            system_prompt=system_prompt,
            executor=executor,
            stop_controller=stop_controller,
            checkpointer=checkpointer
        ).build()
        graph_settings = AgentRuntimeSettings(timeout_seconds=420)
        self._runner = AgentGraphRunner(
            graph=self._compiled_tool_calling,
            settings= graph_settings,
            stop_controller=StopController(),
            trajectory_logger=TrajectoryLogger(graph_settings.trajectory_log_directory)
        )
    
    async def execute(self, context: StepExecutionContext)->BaseStepResult:
        """Виконує контракт AgentWorker - запукає агента для виклику інструментів tool calling"""
        initial_state: StateT = {
            "messages": [HumanMessage(
                content=
                  f"""Виконай поточний крок плану {context.current_step.model_dump_json(indent=2)}"""
                 )
                         ],
             "execution_id": context.execution_id,
             "step_count": 0,
             "used_tokens": 0,
             "execution_status": AnalysisStatus.PENDING,
             "structured_output": None
        }
        thread_id = str(uuid4())
        final_state = await self._runner.run(
            initial_state=initial_state,
            thread_id=thread_id
        )
        response = final_state["structured_output"]
        return HistoricalResearchStepResult.model_validate(response)
        