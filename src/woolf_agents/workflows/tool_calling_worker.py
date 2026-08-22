from collections.abc import Sequence
from .tool_calling_graph import ToolCallingGraph
from src.woolf_agents.runtime.runner import AgentGraphRunner
from typing import TypeVar, Generic
from src.woolf_agents.llm.executor import LLMExecutor
from src.woolf_agents.domains.artifacts.schemas.contracts import StepExecutionContext
from src.woolf_agents.domains.artifacts.schemas.base import BaseStepResult
from src.woolf_agents.runtime.stop_controller import StopController
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.tools import BaseTool
from langgraph.checkpoint.base import BaseCheckpointSaver

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
                 runner: AgentGraphRunner
                 ):
        super().__init__()
        self._compiled_tool_calling: ToolCallingGraph = ToolCallingGraph(
            state=state,
            model=llm,
            tools=tools,
            output_schema=output_schema,
            system_prompt=system_prompt,
            executor=executor,
            stop_controller=stop_controller,
            checkpointer=checkpointer
        ).build()
        self._runner = runner
    
    async def execute(self, context: StepExecutionContext)->BaseStepResult:
        """Виконує контракт AgentWorker - запукає агента для виклику інструментів tool calling"""