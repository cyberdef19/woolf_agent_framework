from .nodes import GraphNode
from typing import Generic, TypeVar, Callable, Literal

StateT = TypeVar("StateT")


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

class ConditionalGraphEdge(Generic[StateT]):
    
    def __init__(self, first_node:GraphNode, routes: dict[str, str], router: Callable[[StateT], str] ):
        super().__init__()
        if not first_node:
            raise ValueError("Має бути вказаний вузол, з якого відбувається вихід потоку виконання")
        if not routes or len(routes) == 0:
            raise ValueError("Має бути вказано бодай один вузол, куди роутер направить потік виконання")
        if not router:
            raise ValueError("Має бути вказано функцію роутер, що спрямовує потік виконання")
            
        self._first_node = first_node
        self._routes = routes
        self._router = router
    
    @property
    def first_node(self) -> GraphNode:
        return self._first_node
    
    @property
    def routes(self) ->dict[str, str]:
        return self._routes
    
    @property
    def router(self) -> Callable[[StateT], str]:
        return self._router
        