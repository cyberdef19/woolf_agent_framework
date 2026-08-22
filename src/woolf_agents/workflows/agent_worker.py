from typing import Protocol
from src.woolf_agents.domains.artifacts.schemas.contracts import StepExecutionContext
from src.woolf_agents.domains.artifacts.schemas.base import BaseStepResult

class AgentWorker(Protocol):
    
    async def execute(self, context: StepExecutionContext) ->BaseStepResult:
        ...