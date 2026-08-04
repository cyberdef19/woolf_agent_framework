from .base_graph import BaseGraph
from .nodes import GraphNode
from .edges import GraphEdge, ConditionalGraphEdge
from typing import Generic, TypeVar, Any
from collections.abc import Sequence
from langchain_core.tools import BaseTool
from langchain_core.messages import SystemMessage
from langgraph.prebuilt import ToolNode
from langgraph.graph import StateGraph, START, END
from langchain_core.language_models.chat_models import BaseChatModel
from src.woolf_agents.runtime.stop_controller import StopController


StateT = TypeVar("StateT")
OutputT = TypeVar("OutputT")



class ToolCallingGraph(
    BaseGraph[StateT],
    Generic[StateT, OutputT]
):
    AGENT_NODE = "agent"
    STOP_GUARD_NODE = "stop_guard"
    TOOLS_NODE = "tools"
    STRUCTURED_OUTPUT_NODE = "structured_output"
    STOPPED_NODE = "stopped"
    
    def __init__(self, 
                 state: type[StateT], 
                 model: BaseChatModel,
                 tools: Sequence[BaseTool],
                 output_schema: type[OutputT],
                 system_prompt: str,
                 stop_controller: StopController
                 ):
        super().__init__(state)
        self._model = model
        if not tools:
            raise ValueError("У граф має бути передано бодай один інструмент")
        self._tools = list(tools)
        self._system_message = SystemMessage(content=system_prompt)
        self._llm_structured_output = model.with_structured_output(output_schema)
        self._tool_model = model.bind_tools(self._tools)
        self._tool_node = ToolNode(self._tools)
        self._stop_controller = stop_controller
    
    async def _agent_node(self, state: StateT)->dict[str, Any]:
        """Вузол формує виклик інструментів"""
        response = await self._tool_model.ainvoke(
           [
               self._system_message,
               *state["messages"]
           ]   
        )
        used_tokens = (
                response.usage_metadata.get("total_tokens", 0)
                if response.usage_metadata
                else 0
                     )
        return {
            "messages": [response],
            "step_count": 1,
            "used_tokens": used_tokens
        }
        
    async def _structured_output_node(self, state: StateT)->dict[str, Any]:
         """Формує структорвану відповідь"""
         response = await self._tool_model.ainvoke(
             [
                 self._system_message,
                 *state["messages"]
             ]   
         )
         return {
             "structured_response": response,
             "execution_status": "completed"
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
            "execution_status": "stopped",
        }    
    
    from typing import Literal


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
        
    from langgraph.graph import END, START


    def _create_edges(self,) -> tuple[GraphEdge, ...]:
        return (
            GraphEdge(
                source=START,
                target=self.AGENT_NODE,
            ),
            GraphEdge(
                source=self.AGENT_NODE,
                target=self.STOP_GUARD_NODE,
            ),
            GraphEdge(
                source=self.TOOLS_NODE,
                target=self.AGENT_NODE,
            ),
            GraphEdge(
                source=self.STRUCTURED_OUTPUT_NODE,
                target=END,
            ),
            GraphEdge(
                source=self.STOPPED_NODE,
                target=END,
            ),
        )
    def _create_conditional_edges(self) -> tuple[ConditionalGraphEdge[StateT], ...]:
        return (
            ConditionalGraphEdge(
                source=self.STOP_GUARD_NODE,
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
        
        
        
      
    
   



                    
