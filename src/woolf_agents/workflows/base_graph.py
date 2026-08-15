from abc import ABC, abstractmethod
from typing import TypeVar, Generic
from langgraph.graph import StateGraph
from langgraph.graph.state import CompiledStateGraph
from .nodes import GraphNode
from .edges import GraphEdge, ConditionalGraphEdge
from src.woolf_agents.runtime.stop_controller import StopController
from src.woolf_agents.llm.executor import LLMExecutor
from collections.abc import Sequence
from langchain_core.tools import BaseTool
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.prebuilt import ToolNode

StateT = TypeVar("StateT")
OutputT = TypeVar("OutputT")
#TargetT = TypeVar("TargetT")


class BaseGraph(ABC, Generic[StateT]):
    
    STOP_GUARD_NODE = "guard"
    TOOLS_NODE = "tools"
    STRUCTURED_OUTPUT_NODE = "structured_output"
    STOPPED_NODE = "stopped"
    
    def __init__(self, 
                state_schema: type[StateT],
                model: BaseChatModel,
                tools: Sequence[BaseTool],
                output_schema: type[OutputT],
                system_prompt: str,
                executor: LLMExecutor,
                stop_controller: StopController
                 ):
        self._state_schema = state_schema
        self._model = model
        if not tools:
            raise ValueError("У граф має бути передано бодай один інструмент")
        self._tools = list(tools)
        self._system_message = SystemMessage(content=system_prompt)
        self._llm_structured_output = model.with_structured_output(output_schema)
        self._tool_model = model.bind_tools(self._tools)
        self._stop_controller = stop_controller
        self._executor = executor
        self._tool_node = ToolNode(self._tools)
    
    @property
    def state_schema(self) ->type[StateT]:
        return self._state_schema
    
    def build(self) -> CompiledStateGraph:
        builder = StateGraph(self._state_schema)
        
        nodes = self._create_nodes()
        edges = self._create_edges()
        conditional_edges = self._create_conditional_edges()
        
        self._register_nodes(builder=builder, nodes=nodes)
        self._register_edges(builder=builder, edges=edges)
        self._register_conditional_edges(builder=builder, conditional_edges=conditional_edges)
        
        return builder.compile()
    
    @abstractmethod
    def _create_nodes(self) -> tuple[GraphNode[StateT],...]:
        """Декларативно створюємо workflow вузли"""
    
    @abstractmethod
    def _create_edges(self) -> tuple[GraphEdge,...]:
        """Декларативно створюємо ребра графа"""
    
    @abstractmethod
    def _create_conditional_edges(self) -> tuple[ConditionalGraphEdge[StateT], ...]:
        """Декларативно створюються умовні ребра графа"""
      
        
    def _register_nodes(self, builder:StateGraph, nodes: tuple[GraphNode[StateT],...]):
        for node in nodes:
            builder.add_node(
                node.name_node,
                node.func
            )
            
    def _register_edges(self, builder: StateGraph, edges: tuple[GraphEdge, ...]):
        for edge in edges:
            builder.add_edge(
                edge.first_node,
                edge.second_node
            )
    
    def _register_conditional_edges(self, builder: StateGraph, conditional_edges:tuple[ConditionalGraphEdge, ...]):
        for edge in conditional_edges:
            builder.add_conditional_edges(
                edge.first_node,
                edge.router,
                edge.routes
            )
    
    
    
    