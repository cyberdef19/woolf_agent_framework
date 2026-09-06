from src.woolf_agents.core.guardrails.tools_allow import ToolGuard

from .base_graph import BaseGraph
from .nodes import GraphNode
from typing import Literal
from langgraph.graph import END, START
from .edges import GraphEdge, ConditionalGraphEdge
from typing import Generic, TypeVar, Any
from collections.abc import Sequence
from langchain_core.tools import BaseTool
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import StateGraph, START, END
from langchain_core.language_models.chat_models import BaseChatModel
from src.woolf_agents.runtime.stop_controller import StopController
from src.woolf_agents.llm.executor import LLMExecutor
import time
from pydantic import ValidationError
from langgraph.checkpoint.base import BaseCheckpointSaver
from .state import AnalysisStatus


StateT = TypeVar("StateT")
OutputT = TypeVar("OutputT")



class ToolCallingGraph(
    BaseGraph[StateT],
    Generic[StateT, OutputT]
):
    AGENT_NODE = "agent"

    
    def __init__(self, 
                 tool_guard: ToolGuard,
                 state: type[StateT], 
                 model: BaseChatModel,
                 tools: Sequence[BaseTool],
                 output_schema: type[OutputT],
                 system_prompt: str,
                 executor: LLMExecutor,
                 stop_controller: StopController,
                 checkpointer: BaseCheckpointSaver
                 ):
        super().__init__(
            state_schema=state,
            model=model,
            tools=tools,
            output_schema=output_schema,
            system_prompt=system_prompt,
            executor=executor,
            stop_controller=stop_controller,
            checkpointer=checkpointer
            )
        self._tool_guard = tool_guard
    
    async def _agent_node(self, state: StateT)->dict[str, Any]:
        #print("\nAGENT NODE MESSAGES:")

        """for message in state["messages"]:
            print(
                type(message).__name__,
                getattr(message, "content", None),
            )"""
        #started_at = time.perf_counter()

        #print("LLM START") 
        try:
            """Вузол формує виклик інструментів"""
            response = await self._executor.model_invoke(
                                         self._tool_model,
                                         [
                                                self._system_message,
                                                *state["messages"],
                                                
                                         ] 
                                         )
            # Guard перевіряє сформовані LLM tool calls
            for tool_call in response.tool_calls:
                self._tool_guard.validate(
                    tool_name=tool_call["name"],
                    arguments=tool_call["args"],
                )
            used_tokens = response.usage_metadata.get("total_tokens", 0) if response.usage_metadata else 0
            return {
                        "messages": [response],
                        "step_count": 1,
                        "used_tokens": used_tokens
                    }
        except Exception as exc:
            print(
                "LLM ERROR:",
                type(exc).__name__,
                str(exc),
                )
            raise
                      
            
        
        
    async def _structured_output_node(self, state: StateT)->dict[str, Any]:
            """Формує структоровану відповідь"""
            
            structured_output_system_message = SystemMessage(
                                                    content="""
                                                    Ти формуєш фінальний структурований результат виконання агента.

                                                    Поверни відповідь ВИКЛЮЧНО як валідний JSON-об'єкт,
                                                    що відповідає наданій JSON Schema.

                                                    Правила:
                                                    - не використовуй Markdown;
                                                    - не використовуй ```json;
                                                    - не додавай текст до або після JSON;
                                                    - не додавай пояснення;
                                                    - використовуй лише дані з результатів інструментів;
                                                    - не вигадуй відсутні значення;
                                                    - значення enum повинні точно відповідати схемі.

                                                    Відповідь повинна починатися символом { і закінчуватися }.
                                                    """
                                                    )
            response = await self._executor.model_invoke(
                    self._llm_structured_output,
                    [
                        structured_output_system_message,
                        *state["messages"],
                        HumanMessage(
                                content=(
                                        "На основі наведених вище результатів сформуй "
                                        "фінальний результат. Поверни виключно JSON, "
                                        "що відповідає заданій схемі."
                                    )
                                ),
                        
                    ] 
                    )
           
            return {
                "structured_output": response,
                "execution_status": AnalysisStatus.COMPLETED
            }
        
    
            
    async def _stop_guard_node(self, state: StateT) -> dict[str, Any]:
        last_message = state["messages"][-1]
        
        decision = self._stop_controller.evaluate(
            completed_steps= state.get("step_count", 0),
            used_tokens= state.get("used_tokens", 0),
            tool_calls=getattr(
                last_message,
                "tool_calls",
                [],
            ),
        )

        return {
            "stop_decision": decision,
        }
    
    async def _stopped_node(self, state: StateT) -> dict[str, Any]:
        return {
            "execution_status": AnalysisStatus.STOPPED,
        }    
    


    def _route_after_guard(self, state: StateT) -> Literal[
                                                            "tools",
                                                            "structured_output",
                                                            "stopped",
                                                           ]:
        """Вибір маршрута потоку виконання після оцінки stop conditions."""

        stop_decision = state.get("stop_decision")

        if (
            stop_decision is not None
            and stop_decision.should_stop
        ):
            return self.STOPPED_NODE

        messages = state["messages"]

        if not messages:
            raise ValueError(
                "Workflow state не отримав повідомлень"
            )

        last_message = messages[-1]

        if getattr(last_message, "tool_calls", None):
            return self.TOOLS_NODE

        return self.STRUCTURED_OUTPUT_NODE
    
    def _create_nodes(self)->tuple[GraphNode[StateT],...]:
        return (
            GraphNode(
                name_node=self.AGENT_NODE,
                func= self._agent_node
            ),
            GraphNode(
                name_node=self.STRUCTURED_OUTPUT_NODE,
                func = self._structured_output_node
            ),
            GraphNode(
                name_node=self.STOP_GUARD_NODE,
                func=self._stop_guard_node
            ),
            GraphNode(
                name_node=self.STOPPED_NODE,
                func=self._stopped_node
            ),
            GraphNode(
                name_node=self.TOOLS_NODE,
                func=self._tool_node
            )
        )
        

    def _create_edges(self,) -> tuple[GraphEdge, ...]:
        return (
            GraphEdge(
                first_node=START,
                second_node=self.AGENT_NODE,
            ),
            GraphEdge(
                first_node=self.AGENT_NODE,
                second_node=self.STOP_GUARD_NODE,
            ),
            GraphEdge(
                first_node=self.TOOLS_NODE,
                second_node=self.AGENT_NODE,
            ),
            GraphEdge(
                first_node=self.STRUCTURED_OUTPUT_NODE,
                second_node=END,
            ),
            GraphEdge(
                first_node=self.STOPPED_NODE,
                second_node=END,
            ),
        )
    def _create_conditional_edges(self) -> tuple[ConditionalGraphEdge[StateT], ...]:
        return (
            ConditionalGraphEdge(
                first_node=self.STOP_GUARD_NODE,
                router=self._route_after_guard,
                routes={
                    self.TOOLS_NODE: self.TOOLS_NODE,
                    self.STRUCTURED_OUTPUT_NODE: (
                        self.STRUCTURED_OUTPUT_NODE
                    ),
                    self.STOPPED_NODE: self.STOPPED_NODE,
                },
            ),
        )
        
        
        
      
    
   



                    
