from typing import Protocol, TypeVar, Generic
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import SystemMessage, HumanMessage
from src.woolf_agents.llm.executor import LLMExecutor

from abc import ABC, abstractmethod

ResultT = TypeVar("ResultT")
ContextT = TypeVar("ContextT")

class AgentWorker(Protocol[ResultT, ContextT]):
    
    async def execute(self, context: ContextT) ->ResultT:
        ...

class AbstractAgentWorker(
    ABC,
    Generic[ResultT, ContextT]
):
    def __init__(self,
                 model: BaseChatModel,
                 executor: LLMExecutor,
                 output_schema: type[ResultT],
                 system_message: SystemMessage
                 ):
        self._output_schema = output_schema
        self._model_with_structured_output = model.with_structured_output(output_schema)
        self._executor = executor
        self._system_message = system_message
    
    @abstractmethod
    def _get_message(self, context: ContextT) -> str:
        ...
    
    async def execute(self, context: ContextT) ->ResultT:
        """Виконує дію від llm та повертає структурований об' єкт"""
        message = self._get_message(context=context)
        response = await self._executor.model_invoke(
                    self._model_with_structured_output,
                    [
                        self._system_message,
                        HumanMessage(
                            content=message
                        )
                    ]
                )   
        return self._output_schema.model_validate(response) 
        
        