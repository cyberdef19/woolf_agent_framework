from .base_graph import BaseGraph
from .nodes import GraphNode
from .edges import GraphEdge, ConditionalGraphEdge
from typing import Generic, TypeVar
from collections.abc import Sequence
from langchain_core.tools import BaseTool
from langchain_core.messages import SystemMessage
from langgraph.prebuilt import ToolNode
from langgraph.graph import StateGraph
from langchain_core.language_models.chat_models import BaseChatModel
from src.woolf_agents.runtime.stop_controller import StopController


StateT = TypeVar("StateT")
OutputT = TypeVar("OutputT")

class ToolCallingGraph(
    BaseGraph[StateT],
    Generic[StateT, OutputT]
):
    
    def __init__(self, 
                 state: type[StateT], 
                 model: BaseChatModel,
                 tools: Sequence[BaseTool],
                 output_schema: type[OutputT],
                 system_prompt: str,
                 stop_controller: StopController,
                 nodes: list[GraphNode],
                 edges: list[GraphEdge],
                 conditional_edges: list[ConditionalGraphEdge] 
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
        self._nodes = nodes
        self._edges = edges
        self._conditional_edges = conditional_edges
    
    def _add_nodes(self, builder: StateGraph) -> None:
        
        for node in self._nodes:
            builder.add_node(
                node.name_node,
                node.func
            )
    
    def _add_edges(self, builder)->None:
        
        for edge in self._edges:
            builder.add_edge(
                edge.first_node.name_node,
                edge.second_node.name_node
            )

        for cedge in self._conditional_edges:
            path_map: dict = {node:node for node in cedge.nodes}
            builder.add_conditional_edges(
                cedge.first_node.name_node,
                cedge.func,
                path_map
            )