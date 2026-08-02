from typing import Generic, TypeVar, Callable

StateT = TypeVar("StateT")
    
class GraphNode(Generic[StateT]):
    
    def __init__(self, name_node: str, func: Callable[[StateT], dict]):
        super().__init__()
        if not name_node:
            raise ValueError("Недопустиме значення для назви вузла")
        self._name_node = name_node
        self._func = func
    
    @property
    def name_node(self) ->str:
        return self._name_node
    
    @property
    def func(self) ->Callable[[StateT], dict]:
        return self._func


        