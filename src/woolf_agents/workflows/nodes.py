from typing import Generic, TypeVar, Callable, TypeAlias, Any, Awaitable

StateT = TypeVar("StateT")
NodeUpdate: TypeAlias = dict[str, Any]

NodeHandler: TypeAlias = Callable[
    [StateT],
    NodeUpdate | Awaitable[NodeUpdate],
]

    
class GraphNode(Generic[StateT]):
    
    def __init__(self, name_node: str, func: NodeHandler[StateT]):
        super().__init__()
        if not name_node:
            raise ValueError("Недопустиме значення для назви вузла")
        self._name_node = name_node
        self._func = func
    
    @property
    def name_node(self) ->str:
        return self._name_node
    
    @property
    def func(self) ->NodeHandler[StateT]:
        return self._func


        