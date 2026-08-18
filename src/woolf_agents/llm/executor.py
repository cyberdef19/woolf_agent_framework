from langchain_core.language_models.chat_models import BaseChatModel
from src.woolf_agents.core.retry import RetryPolicyAgent
from langchain_core.messages import BaseMessage, AIMessage
import asyncio
from pydantic import ValidationError
from typing import Any

class LLMExecutor:
    
    def __init__(self, retry_agent: RetryPolicyAgent, llm_timeout_seconds:float):
        self._retry_agent: RetryPolicyAgent = retry_agent
        self._llm_timeout_seconds: float = llm_timeout_seconds
    
    async def model_invoke(self, model: BaseChatModel, messages:list[BaseMessage])->Any:
        
            async for attempt in self._retry_agent.create_retrying():
                with attempt:
                    async with asyncio.timeout(self._llm_timeout_seconds):
                        response = await model.ainvoke(
                            messages
                        ) 

                        return response
            raise RuntimeError("LLM виконано без результату")
        