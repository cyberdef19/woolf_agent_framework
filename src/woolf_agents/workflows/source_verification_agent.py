
from src.woolf_agents.domains.artifacts.schemas.contracts import HistoricalResearchExecutionResult, SourceVerificationResult
from src.woolf_agents.llm.executor import LLMExecutor
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain.chat_models import BaseChatModel

from src.woolf_agents.workflows.state import MASAgentState
from collections.abc import Sequence
from langchain.tools import BaseTool
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage


class SourceVerificationAgent:
    
    def __init__(
        self,
        model: BaseChatModel,
        system_prompt: str,
        mcp_client: MultiServerMCPClient,
        tools: Sequence[BaseTool]
        ):
        
        self._model = model
        self._system_prompt = system_prompt
        self._mcp_client = mcp_client
        self._tools = tools
        
        self._agent = create_agent(
            model=self._model,
            tools=self._tools,
            system_prompt=self._system_prompt,
            response_format=SourceVerificationResult
        )
    
    
    async def execute(self, state: MASAgentState) ->SourceVerificationResult:
        """Верифікує джерела за доказовою базою дослідження"""
        research_result:HistoricalResearchExecutionResult = MASAgentState(state).get("research_result")
        user_task: str = MASAgentState(state).get("task_user")
        methodology = self._mcp_client.get_resources(
            "historical",
            "heritage://research/methodology"
        )
        messages = self._mcp_client.get_prompt(
            "historical",
            "verification_sources",
            arguments={
                "user_task": user_task,
                "research_result": research_result.model_dump_json(),
                "methodology": methodology
            }
        )
        
        result = await self._agent.ainvoke(
            {
                "messages":messages
            }
        )
        return result["structured_otput"]
        

        
        
    
    
        
        