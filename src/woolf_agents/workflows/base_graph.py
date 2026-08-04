from abc import ABC, abstractmethod
from typing import TypeVar, Generic
from langgraph.graph import StateGraph
from langgraph.graph.state import CompiledStateGraph
from .nodes import GraphNode
from .edges import GraphEdge, ConditionalGraphEdge


StateT = TypeVar("StateT")
TargetT = TypeVar("TargetT")


class BaseGraph(ABC, Generic[StateT]):
    
    def __init__(self, state_schema: type[StateT]):
        self._state_schema = state_schema
    
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
    
    
    
    