from abc import ABC, abstractmethod
from typing import TypeVar, Generic
from langgraph.graph import StateGraph
from langgraph.graph.state import CompiledStateGraph

StateT = TypeVar("StateT")


class BaseGraph(ABC, Generic[StateT]):
    
    def __abs__(self, state_schema: type[StateT]):
        self._state_schema = state_schema
    
    @property
    def state_schema(self) ->type[StateT]:
        return self._state_schema
    
    def build(self) -> CompiledStateGraph:
        builder = StateGraph(self._state_schema)
        
        self._add_nodes(builder)
        self._add_edges(builder)
        
        return builder.compile()
    
    @abstractmethod
    def _add_nodes(self, builder: StateGraph) -> None:
        """ Додає вузли в граф"""
    
    def _add_edges(self, builder: StateGraph) -> None:
        """ Додає ребра у граф"""
    
    