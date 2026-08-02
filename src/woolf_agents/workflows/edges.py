from .nodes import GraphNode
from typing import Generic, TypeVar, Callable, Literal

StateT = TypeVar("StateT")
TargetT = TypeVar("TargetT", bound=str)

class GraphEdge:
    
    def __init__(self, first_node: GraphNode, second_node:GraphNode):
        if not first_node or not second_node:
            raise ValueError("Вузли не мають бути None")
        self._first_node = first_node
        self._second_node = second_node
    
    @property
    def first_node(self) ->GraphNode:
        return self._first_node
    
    @property
    def second_node(self) ->GraphNode:
        return self._second_node

class ConditionalGraphEdge(Generic[StateT, TargetT]):
    
    def __init__(self, first_node:GraphNode, nodes: list[GraphNode], func: Callable[[StateT], TargetT], ):
        super().__init__()
        if not first_node:
            raise ValueError("Має бути вказаний вузол, з якого відбувається вихід потоку виконання")
        if not nodes or len(nodes) == 0:
            raise ValueError("Має бути вказано бодай один вузол, куди роутер направить потік виконання")
        if not func:
            raise ValueError("Має бути вказано функцію роутер, що спрямовує потік виконання")
            
        self._first_node = first_node
        self._nodes = nodes
        self._func = func
    
    @property
    def first_node(self) -> GraphNode:
        return self._first_node
    
    @property
    def nodes(self) ->list[GraphNode]:
        return self._nodes
    
    @property
    def func(self) -> Callable[[StateT], TargetT]:
        return self._func
        